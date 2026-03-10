from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.api.schemas.campaigns import CampaignCreate, CampaignDetailOut, CampaignOut, VariantDetailOut
from app.api.schemas.metrics import MetricOut
from app.api.schemas.variants import VariantOut
from app.api.schemas.ai import GenerateVariantsRequest

from app.db.models import CampaignStatus
from app.db.repos.campaigns_repo import CampaignsRepo
from app.db.repos.variants_repo import VariantsRepo
from app.db.repos.logs_repo import LogsRepo

from app.services.openai_service import generate_variant_pack

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class CampaignStatusUpdate(CampaignCreate.model_config.__class__):
    pass


@router.post("", response_model=CampaignOut, status_code=201)
async def create_campaign(
    payload: CampaignCreate,
    session: AsyncSession = Depends(get_db_session),
):
    obj = await CampaignsRepo.create(
        session,
        name=payload.name,
        channel=payload.channel,
        country=payload.country,
        product=payload.product.model_dump(),
        objective=payload.objective,
        status=payload.status,
        user_id=None,  # sin auth por ahora
    )
    return CampaignOut.model_validate(obj)


@router.get("", response_model=List[CampaignOut])
async def list_campaigns(
    session: AsyncSession = Depends(get_db_session),
    status: Optional[CampaignStatus] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    items = await CampaignsRepo.list(session, status=status, limit=limit, offset=offset)
    return [CampaignOut.model_validate(x) for x in items]


@router.get("/{campaign_id}", response_model=CampaignDetailOut)
async def get_campaign_detail(
    campaign_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    campaign = await CampaignsRepo.get(session, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    rows = await VariantsRepo.list_for_campaign_with_latest_metric(
        session, campaign_id=campaign_id, limit=limit, offset=offset
    )

    variants_out: list[VariantDetailOut] = []
    for variant, metric in rows:
        v = VariantOut.model_validate(variant)
        m = MetricOut.model_validate(metric) if metric else None
        variants_out.append(VariantDetailOut(**v.model_dump(), latest_metric=m))

    base = CampaignOut.model_validate(campaign)
    return CampaignDetailOut(**base.model_dump(), variants=variants_out)


@router.patch("/{campaign_id}", response_model=CampaignOut)
async def update_campaign_status(
    campaign_id: uuid.UUID,
    payload: dict,  # simple por ahora: {"status":"paused"} etc.
    session: AsyncSession = Depends(get_db_session),
):
    if "status" not in payload:
        raise HTTPException(status_code=400, detail="Missing 'status' field")

    try:
        new_status = CampaignStatus(payload["status"])
    except Exception:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid status",
                "allowed": [s.value for s in CampaignStatus],
            },
        )

    updated = await CampaignsRepo.update_status(session, campaign_id=campaign_id, status=new_status)
    if not updated:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return CampaignOut.model_validate(updated)


@router.post("/{campaign_id}/variants/generate", response_model=list[VariantOut], status_code=201)
async def generate_variants(
    campaign_id: uuid.UUID,
    payload: GenerateVariantsRequest,
    session: AsyncSession = Depends(get_db_session),
):
    campaign = await CampaignsRepo.get(session, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign_context = {
        "product_name": campaign.product.get("name"),
        "price_cop": campaign.product.get("price_cop"),
        "country": campaign.country,
        "channel": campaign.channel.value,
        "objective": campaign.objective.value,
    }

    pack = await generate_variant_pack(campaign_context=campaign_context, user_prompt=payload.user_prompt)

    creatives: list[dict] = []
    for v in pack.variants:
        c = v.model_dump()
        c.setdefault("image_url", None)
        creatives.append(c)

    external_template = {
        "provider": "meta",
        "post_id": None,
        "post_url": None,
        "published_at": None,
    }

    created = await VariantsRepo.create_many(
        session,
        campaign_id=campaign_id,
        creatives=creatives,
        external_template=external_template,
    )

    await LogsRepo.create(
        session,
        agent="create",
        campaign_id=campaign_id,
        input={"campaign_context": campaign_context, "user_prompt": payload.user_prompt},
        output=pack.model_dump(),
        reason=None,
    )

    return [VariantOut.model_validate(x) for x in created]