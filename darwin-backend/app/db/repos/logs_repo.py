from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentLog


class LogsRepo:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        agent: str,
        input: dict,
        output: dict,
        reason: str | None = None,
        campaign_id: Optional[uuid.UUID] = None,
        variant_id: Optional[uuid.UUID] = None,
    ) -> AgentLog:
        obj = AgentLog(
            agent=agent,
            input=input,
            output=output,
            reason=reason,
            campaign_id=campaign_id,
            variant_id=variant_id,
        )
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    @staticmethod
    async def list_latest(
        session: AsyncSession,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentLog]:
        stmt = select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit).offset(offset)
        res = await session.execute(stmt)
        return list(res.scalars().all())