from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SchedulerSettings


class SchedulerRepo:
    @staticmethod
    async def get(session: AsyncSession) -> SchedulerSettings | None:
        stmt = select(SchedulerSettings).where(SchedulerSettings.id == 1)
        res = await session.execute(stmt)
        return res.scalars().first()

    @staticmethod
    async def get_or_create_default(
        session: AsyncSession,
        *,
        default_enabled: bool,
        default_interval_seconds: int,
    ) -> SchedulerSettings:
        row = await SchedulerRepo.get(session)
        if row:
            return row

        row = SchedulerSettings(
            id=1,
            enabled=default_enabled,
            interval_seconds=default_interval_seconds,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def update(
        session: AsyncSession,
        *,
        enabled: bool | None = None,
        interval_seconds: int | None = None,
    ) -> SchedulerSettings:
        row = await SchedulerRepo.get(session)
        if not row:
            row = SchedulerSettings(id=1, enabled=True, interval_seconds=120)
            session.add(row)
            await session.commit()
            await session.refresh(row)

        if enabled is not None:
            row.enabled = enabled
        if interval_seconds is not None:
            row.interval_seconds = interval_seconds

        await session.commit()
        await session.refresh(row)
        return row