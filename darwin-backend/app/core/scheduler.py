from __future__ import annotations

import os
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from app.api.schemas.darwin import DarwinRunRequest
from app.db.models import VariantStatus
from app.db.repos.logs_repo import LogsRepo
from app.db.repos.metrics_repo import MetricsRepo
from app.db.repos.variants_repo import VariantsRepo
from app.db.session import AsyncSessionLocal
from app.services.darwin_service import run_darwin
from app.services.fitness_service import compute_fitness
from app.services.providers.meta_provider import MetaAPIError, get_meta_provider

load_dotenv()
logger = logging.getLogger("scheduler")

_scheduler: AsyncIOScheduler | None = None


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


async def _refresh_metrics_for_all_published() -> None:
    """
    Refresca métricas para todas las variants 'published' y guarda snapshot + fitness.
    """
    provider = get_meta_provider()

    async with AsyncSessionLocal() as session:
        variants = await VariantsRepo.list_by_status(session, status=VariantStatus.published, limit=500, offset=0)

        for v in variants:
            external = v.external or {}
            post_id = external.get("post_id")
            if not post_id:
                continue

            try:
                counts = await provider.fetch_post_counts(post_id=str(post_id))
                likes = int(counts.get("likes", 0))
                comments = int(counts.get("comments", 0))
                shares = int(counts.get("shares", 0))

                # MVP orgánico:
                impressions = 0
                clicks = 0

                fitness = compute_fitness(likes=likes, comments=comments, shares=shares, clicks=clicks)

                metric = await MetricsRepo.create_snapshot(
                    session,
                    variant_id=v.id,
                    impressions=impressions,
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    clicks=clicks,
                    fitness=fitness,
                )

                await LogsRepo.create(
                    session,
                    agent="metrics_cron",
                    campaign_id=v.campaign_id,
                    variant_id=v.id,
                    input={"post_id": str(post_id)},
                    output={"counts": counts, "fitness": fitness, "metric_id": str(metric.id)},
                    reason=None,
                )

            except MetaAPIError as e:
                # Guardamos el error en logs (no tumbamos el cron)
                await LogsRepo.create(
                    session,
                    agent="metrics_cron",
                    campaign_id=v.campaign_id,
                    variant_id=v.id,
                    input={"post_id": str(post_id)},
                    output={"error": {"status_code": e.status_code, "payload": e.payload}},
                    reason="meta_metrics_failed",
                )
            except Exception as e:
                await LogsRepo.create(
                    session,
                    agent="metrics_cron",
                    campaign_id=v.campaign_id,
                    variant_id=v.id,
                    input={"post_id": str(post_id)},
                    output={"error": str(e)},
                    reason="unexpected_error",
                )


async def _darwin_tick() -> None:
    """
    Tick completo:
      1) refresh metrics de published
      2) run darwin
    """
    await _refresh_metrics_for_all_published()

    threshold_up = _env_float("DARWIN_THRESHOLD_UP", 5.0)
    threshold_down = _env_float("DARWIN_THRESHOLD_DOWN", -3.0)
    delete_remote = _env_bool("DARWIN_DELETE_REMOTE_POST", True)

    async with AsyncSessionLocal() as session:
        try:
            await run_darwin(
                session,
                DarwinRunRequest(
                    threshold_up=threshold_up,
                    threshold_down=threshold_down,
                    dry_run=False,
                    delete_remote_post=delete_remote,
                ),
            )
        except Exception as e:
            # Log global del tick
            logger.exception("Darwin run failed: %s", e)
            await LogsRepo.create(
                session,
                agent="darwin_cron",
                input={"threshold_up": threshold_up, "threshold_down": threshold_down, "delete_remote_post": delete_remote},
                output={"error": str(e)},
                reason="darwin_failed",
                campaign_id=None,
                variant_id=None,
            )


def start_scheduler() -> None:
    global _scheduler

    enabled = _env_bool("SCHEDULER_ENABLED", True)
    if not enabled:
        logger.info("Scheduler disabled by SCHEDULER_ENABLED=false")
        return

    if _scheduler and _scheduler.running:
        return

    interval = _env_int("SCHEDULER_INTERVAL_SECONDS", 120)

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        _darwin_tick,
        trigger="interval",
        seconds=interval,
        id="darwin_tick",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=30,
    )
    _scheduler.start()
    logger.info("Scheduler started. Interval=%ss", interval)


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    _scheduler = None