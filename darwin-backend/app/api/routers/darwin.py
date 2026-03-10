from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.api.schemas.darwin import DarwinRunRequest, DarwinRunResult
from app.services.darwin_service import run_darwin

router = APIRouter(prefix="/darwin", tags=["darwin"])


@router.post("/run", response_model=DarwinRunResult)
async def darwin_run(payload: DarwinRunRequest, session: AsyncSession = Depends(get_db_session)):
    return await run_darwin(session, payload)