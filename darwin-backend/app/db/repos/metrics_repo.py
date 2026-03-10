from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import VariantMetric


class MetricsRepo:
    @staticmethod
    async def create_snapshot(
        session: AsyncSession,
        *,
        variant_id: uuid.UUID,
        impressions: int = 0,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        clicks: int = 0,
        fitness: float = 0.0,
    ) -> VariantMetric:
        obj = VariantMetric(
            variant_id=variant_id,
            impressions=impressions,
            likes=likes,
            comments=comments,
            shares=shares,
            clicks=clicks,
            fitness=fitness,
        )
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    @staticmethod
    async def latest_for_variant(session: AsyncSession, variant_id: uuid.UUID) -> VariantMetric | None:
        stmt = (
            select(VariantMetric)
            .where(VariantMetric.variant_id == variant_id)
            .order_by(VariantMetric.computed_at.desc())
            .limit(1)
        )
        res = await session.execute(stmt)
        return res.scalars().first()

    @staticmethod
    async def list_for_variant(
        session: AsyncSession,
        *,
        variant_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[VariantMetric]:
        stmt = (
            select(VariantMetric)
            .where(VariantMetric.variant_id == variant_id)
            .order_by(VariantMetric.computed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())