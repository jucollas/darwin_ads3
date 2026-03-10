from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.darwin import DarwinRunRequest, DarwinRunResult
from app.db.models import VariantStatus
from app.db.repos.logs_repo import LogsRepo
from app.db.repos.metrics_repo import MetricsRepo
from app.db.repos.variants_repo import VariantsRepo
from app.services.darwin_service import run_darwin
from app.services.fitness_service import compute_fitness
from app.services.providers.meta_provider import MetaAPIError, get_meta_provider


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "y", "on")


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if not v:
        return default
    return int(v)


async def refresh_metrics_for_all_published(session: AsyncSession) -> int:
    """
    Refresca métricas para TODAS las variants published con post_id.
    Retorna cuántas snapshots se insertaron.
    """
    meta = get_meta_provider()
    published = await VariantsRepo.list_by_status(session, status=VariantStatus.published, limit=500, offset=0)

    created = 0
    for v in published:
        post_id = (v.external or {}).get("post_id")
        if not post_id:
            continue

        try:
            counts = await meta.fetch_post_counts(post_id=str(post_id))
        except MetaAPIError as e:
            await LogsRepo.create(
                session,
                agent="metrics",
                campaign_id=v.campaign_id,
                variant_id=v.id,
                input={"post_id": str(post_id), "source": "scheduler"},
                output={"error": e.payload},
                reason="meta_metrics_failed",
            )
            continue

        likes = int(counts.get("likes", 0))
        comments = int(counts.get("comments", 0))
        shares = int(counts.get("shares", 0))

        impressions = 0
        clicks = 0
        fitness = compute_fitness(likes=likes, comments=comments, shares=shares, clicks=clicks)

        await MetricsRepo.create_snapshot(
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
            agent="metrics",
            campaign_id=v.campaign_id,
            variant_id=v.id,
            input={"post_id": str(post_id), "source": "scheduler"},
            output={"counts": counts, "fitness": fitness},
            reason=None,
        )
        created += 1

    return created


async def run_full_cycle(session: AsyncSession, *, req: DarwinRunRequest | None = None) -> dict:
    """
    1) refresh metrics masivo
    2) darwin.run
    """
    metrics_created = await refresh_metrics_for_all_published(session)

    if req is None:
        req = DarwinRunRequest(
            threshold_up=float(_env_int("DARWIN_THRESHOLD_UP", 5)),
            threshold_down=float(_env_int("DARWIN_THRESHOLD_DOWN", -3)),
            dry_run=False,
            delete_remote_post=_env_bool("DARWIN_DELETE_REMOTE_POST", True),
        )

    darwin_result: DarwinRunResult = await run_darwin(session, req)
    return {"metrics_created": metrics_created, "darwin": darwin_result.model_dump()}