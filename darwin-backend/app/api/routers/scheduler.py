from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.api.schemas.darwin import DarwinRunRequest
from app.db.repos.scheduler_repo import SchedulerRepo
from app.services.cycle_service import run_full_cycle
from app.services.scheduler_manager import scheduler_manager

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class SchedulerConfigOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool
    interval_seconds: int
    runtime: dict


class SchedulerConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool | None = None
    interval_seconds: int | None = Field(default=None, ge=10, le=3600)


@router.get("/config", response_model=SchedulerConfigOut)
async def get_scheduler_config(session: AsyncSession = Depends(get_db_session)):
    row = await SchedulerRepo.get_or_create_default(session, default_enabled=True, default_interval_seconds=120)
    return SchedulerConfigOut(
        enabled=row.enabled,
        interval_seconds=row.interval_seconds,
        runtime=scheduler_manager.status(),
    )


@router.put("/config", response_model=SchedulerConfigOut)
async def update_scheduler_config(payload: SchedulerConfigUpdate, session: AsyncSession = Depends(get_db_session)):
    row = await SchedulerRepo.update(
        session,
        enabled=payload.enabled,
        interval_seconds=payload.interval_seconds,
    )

    # Reprograma el scheduler en caliente
    await scheduler_manager.apply_current_settings()

    return SchedulerConfigOut(
        enabled=row.enabled,
        interval_seconds=row.interval_seconds,
        runtime=scheduler_manager.status(),
    )


@router.post("/run-now")
async def run_now(
    payload: DarwinRunRequest = DarwinRunRequest(),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Ejecuta ciclo completo inmediato:
      1) refresh metrics de published
      2) darwin.run (con thresholds del payload)
    """
    result = await run_full_cycle(session, req=payload)
    return result