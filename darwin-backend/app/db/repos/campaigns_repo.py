from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Campaign, CampaignChannel, CampaignObjective, CampaignStatus


class CampaignsRepo:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        name: str,
        channel: CampaignChannel,
        country: str,
        product: dict,
        objective: CampaignObjective,
        status: CampaignStatus = CampaignStatus.active,
        user_id: Optional[uuid.UUID] = None,
    ) -> Campaign:
        obj = Campaign(
            user_id=user_id,
            name=name,
            channel=channel,
            country=country,
            product=product,
            objective=objective,
            status=status,
        )
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        status: CampaignStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Campaign]:
        stmt = select(Campaign).order_by(Campaign.created_at.desc()).limit(limit).offset(offset)
        if status is not None:
            stmt = stmt.where(Campaign.status == status)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get(session: AsyncSession, campaign_id: uuid.UUID) -> Campaign | None:
        stmt = select(Campaign).where(Campaign.id == campaign_id)
        res = await session.execute(stmt)
        return res.scalars().first()

    @staticmethod
    async def update_status(
        session: AsyncSession,
        *,
        campaign_id: uuid.UUID,
        status: CampaignStatus,
    ) -> Campaign | None:
        obj = await CampaignsRepo.get(session, campaign_id)
        if not obj:
            return None
        obj.status = status
        await session.commit()
        await session.refresh(obj)
        return obj