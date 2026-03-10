from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db.session import AsyncSessionLocal
from app.db.repos.scheduler_repo import SchedulerRepo
from app.services.cycle_service import run_full_cycle


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


class SchedulerManager:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.job_id = "darwin_cycle"
        self.started = False

    async def start(self) -> None:
        if self.started:
            return

        # Crea config por defecto si no existe
        default_enabled = _env_bool("SCHEDULER_ENABLED", True)  # kill switch también aplica
        default_interval = _env_int("SCHEDULER_DEFAULT_INTERVAL_SECONDS", 120)

        async with AsyncSessionLocal() as session:
            settings = await SchedulerRepo.get_or_create_default(
                session,
                default_enabled=default_enabled,
                default_interval_seconds=default_interval,
            )

        # Arranca scheduler (aunque no tenga job todavía)
        self.scheduler.start()
        self.started = True

        # Programa job si corresponde
        await self.apply_current_settings()

    async def shutdown(self) -> None:
        if self.started:
            self.scheduler.shutdown(wait=False)
            self.started = False

    async def apply_current_settings(self) -> None:
        """
        Lee settings de DB y (re)programa job.
        Respeta kill switch env SCHEDULER_ENABLED.
        """
        kill_switch = _env_bool("SCHEDULER_ENABLED", True)

        async with AsyncSessionLocal() as session:
            settings = await SchedulerRepo.get_or_create_default(
                session,
                default_enabled=True,
                default_interval_seconds=_env_int("SCHEDULER_DEFAULT_INTERVAL_SECONDS", 120),
            )

        # Si kill switch está off: no programamos job
        if not kill_switch or not settings.enabled:
            self._remove_job_if_exists()
            return

        # (Re)programa con nuevo intervalo
        self._remove_job_if_exists()
        self.scheduler.add_job(
            self._job_wrapper,
            trigger=IntervalTrigger(seconds=int(settings.interval_seconds)),
            id=self.job_id,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
        )

    def _remove_job_if_exists(self) -> None:
        try:
            self.scheduler.remove_job(self.job_id)
        except Exception:
            pass

    async def _job_wrapper(self) -> None:
        # Job real: abre sesión y corre ciclo completo
        async with AsyncSessionLocal() as session:
            await run_full_cycle(session)

    def status(self) -> dict:
        job = self.scheduler.get_job(self.job_id)
        return {
            "started": self.started,
            "job_scheduled": job is not None,
            "next_run_time": job.next_run_time.astimezone(timezone.utc).isoformat() if job and job.next_run_time else None,
            "now": datetime.now(timezone.utc).isoformat(),
            "kill_switch_env": _env_bool("SCHEDULER_ENABLED", True),
        }


scheduler_manager = SchedulerManager()