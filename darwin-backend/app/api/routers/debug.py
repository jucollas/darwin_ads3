from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.db.models import CampaignChannel, CampaignObjective
from app.db.repos.campaigns_repo import CampaignsRepo
from app.db.repos.variants_repo import VariantsRepo

from app.api.schemas.campaigns import CampaignCreate, CampaignOut


router = APIRouter(prefix="/debug", tags=["debug"])


def _campaign_to_dict(c) -> dict[str, Any]:
    return {
        "id": str(c.id),
        "user_id": str(c.user_id) if c.user_id else None,
        "name": c.name,
        "channel": c.channel.value,
        "country": c.country,
        "product": c.product,
        "objective": c.objective.value,
        "status": c.status.value,
        "created_at": c.created_at.isoformat() if hasattr(c.created_at, "isoformat") else str(c.created_at),
    }


@router.post("/campaigns/create-and-get")
async def create_and_get_campaign(session: AsyncSession = Depends(get_db_session)):
    created = await CampaignsRepo.create(
        session,
        name="Promo Hamburguesa Cali",
        channel=CampaignChannel.facebook_page,
        country="CO",
        product={"name": "Hamburguesa Doble", "price_cop": 22000},
        objective=CampaignObjective.engagement,
    )

    fetched = await CampaignsRepo.get(session, uuid.UUID(str(created.id)))
    return {
        "created": _campaign_to_dict(created),
        "fetched": _campaign_to_dict(fetched) if fetched else None,
    }

@router.post("/campaigns/validate", response_model=CampaignCreate)
async def validate_campaign_payload(payload: CampaignCreate):
    # Solo valida y devuelve el payload
    return payload


@router.get("/error/400")
async def force_400():
    raise HTTPException(status_code=400, detail="Example bad request")



@router.post("/campaigns/{campaign_id}/variants/demo")
async def demo_create_variant(campaign_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)):
    c = await CampaignsRepo.get(session, campaign_id)
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")

    v = await VariantsRepo.create(
        session,
        campaign_id=campaign_id,
        creative={
            "headline": "2x1 SOLO HOY",
            "primary_text": "🔥 Ven por tu 2x1 en Cali…",
            "cta": "Escríbenos",
            "image_prompt": "Banner moderno con hamburguesa…",
            "image_url": None,
        },
        external={"provider": "meta", "post_id": None, "post_url": None, "published_at": None},
    )
    return {"variant_id": str(v.id)}
