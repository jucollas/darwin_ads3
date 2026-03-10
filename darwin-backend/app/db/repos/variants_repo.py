from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Variant, VariantStatus, VariantMetric


class VariantsRepo:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        campaign_id: uuid.UUID,
        creative: dict,
        external: dict | None = None,
        generation: int = 0,
        parent_variant_id: Optional[uuid.UUID] = None,
        status: VariantStatus = VariantStatus.draft,
    ) -> Variant:
        obj = Variant(
            campaign_id=campaign_id,
            generation=generation,
            parent_variant_id=parent_variant_id,
            status=status,
            creative=creative,
            external=external or {},
        )
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    @staticmethod
    async def get(session: AsyncSession, variant_id: uuid.UUID) -> Variant | None:
        stmt = select(Variant).where(Variant.id == variant_id)
        res = await session.execute(stmt)
        return res.scalars().first()

    @staticmethod
    async def list_for_campaign(
        session: AsyncSession,
        *,
        campaign_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Variant]:
        stmt = (
            select(Variant)
            .where(Variant.campaign_id == campaign_id)
            .order_by(Variant.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def update_status(
        session: AsyncSession,
        *,
        variant_id: uuid.UUID,
        status: VariantStatus,
    ) -> Variant | None:
        obj = await VariantsRepo.get(session, variant_id)
        if not obj:
            return None
        obj.status = status
        await session.commit()
        await session.refresh(obj)
        return obj

    @staticmethod
    async def set_external(
        session: AsyncSession,
        *,
        variant_id: uuid.UUID,
        external: dict,
    ) -> Variant | None:
        obj = await VariantsRepo.get(session, variant_id)
        if not obj:
            return None
        obj.external = external
        await session.commit()
        await session.refresh(obj)
        return obj

    @staticmethod
    async def list_for_campaign_with_latest_metric(
        session: AsyncSession,
        *,
        campaign_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[tuple[Variant, VariantMetric | None]]:
        """
        Devuelve (Variant, LatestMetric|None) por cada variant del campaign.
        Solución: correlacionar explícitamente el subquery con Variant.
        """
        latest_metric_id = (
            select(VariantMetric.id)
            .where(VariantMetric.variant_id == Variant.id)
            .order_by(VariantMetric.computed_at.desc())
            .limit(1)
            .correlate(Variant)  # <-- CLAVE: evita auto-correlation sin FROM
            .scalar_subquery()
        )

        stmt = (
            select(Variant, VariantMetric)
            .outerjoin(VariantMetric, VariantMetric.id == latest_metric_id)
            .where(Variant.campaign_id == campaign_id)
            .order_by(Variant.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        res = await session.execute(stmt)
        return list(res.all())

    @staticmethod
    async def create_many(
        session: AsyncSession,
        *,
        campaign_id: uuid.UUID,
        creatives: list[dict],
        external_template: dict,
        generation: int = 0,
        parent_variant_id: Optional[uuid.UUID] = None,
        status: VariantStatus = VariantStatus.draft,
    ) -> list[Variant]:
        objs: list[Variant] = []
        for creative in creatives:
            objs.append(
                Variant(
                    campaign_id=campaign_id,
                    generation=generation,
                    parent_variant_id=parent_variant_id,
                    status=status,
                    creative=creative,
                    external=dict(external_template),
                )
            )

        session.add_all(objs)
        await session.commit()
        for o in objs:
            await session.refresh(o)
        return objs

    @staticmethod
    async def set_status_and_external(
        session: AsyncSession,
        *,
        variant_id: uuid.UUID,
        status: VariantStatus,
        external: dict,
    ) -> Variant | None:
        obj = await VariantsRepo.get(session, variant_id)
        if not obj:
            return None
        obj.status = status
        obj.external = external
        await session.commit()
        await session.refresh(obj)
        return obj

    @staticmethod
    async def list_by_status(
        session: AsyncSession,
        *,
        status: VariantStatus,
        limit: int = 500,
        offset: int = 0,
    ) -> list[Variant]:
        stmt = (
            select(Variant)
            .where(Variant.status == status)
            .order_by(Variant.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())    