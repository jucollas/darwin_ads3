from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.api.schemas.variants import VariantOut
from app.api.schemas.metrics import MetricOut
from app.api.schemas.variants import VariantUnpublishRequest

from app.db.models import CampaignChannel, VariantStatus

from app.db.repos.campaigns_repo import CampaignsRepo
from app.db.repos.logs_repo import LogsRepo
from app.db.repos.variants_repo import VariantsRepo
from app.db.repos.metrics_repo import MetricsRepo

from app.services.providers.meta_provider import MetaAPIError, get_meta_provider
from app.services.fitness_service import compute_fitness




router = APIRouter(prefix="/variants", tags=["variants"])


def build_facebook_message(creative: dict[str, Any]) -> str:
    """
    Construye el 'message' del post a partir del creative mínimo:
    headline, primary_text, cta.
    """
    headline = creative.get("headline", "").strip()
    primary = creative.get("primary_text", "").strip()
    cta = creative.get("cta", "").strip()

    lines = []
    if headline:
        lines.append(f"✨ {headline}")
    if primary:
        lines.append(primary)
    if cta:
        lines.append(f"👉 {cta}")

    return "\n\n".join(lines).strip()


@router.post("/{variant_id}/publish", response_model=VariantOut)
async def publish_variant(
    variant_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
):
    variant = await VariantsRepo.get(session, variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    if variant.status != VariantStatus.draft:
        raise HTTPException(status_code=400, detail="Variant must be in 'draft' status to publish")

    campaign = await CampaignsRepo.get(session, variant.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # MVP: solo soportamos Facebook Page
    if campaign.channel != CampaignChannel.facebook_page:
        raise HTTPException(status_code=400, detail="Only 'facebook_page' channel is supported in this MVP")

    message = build_facebook_message(variant.creative)

    provider = get_meta_provider()
    try:
        pub = await provider.publish_variant(message=message)
    except MetaAPIError as e:
        # Meta es un upstream => 502 para el frontend, con detalles
        raise HTTPException(status_code=502, detail={"message": "Meta publish failed", "meta": e.payload})

    external = {
        "provider": "meta",
        "post_id": pub.get("post_id"),
        "post_url": pub.get("post_url"),
        "published_at": datetime.now(timezone.utc).isoformat(),
    }

    updated = await VariantsRepo.set_status_and_external(
        session,
        variant_id=variant_id,
        status=VariantStatus.published,
        external=external,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Variant not found (race condition)")

    await LogsRepo.create(
        session,
        agent="publish",
        campaign_id=campaign.id,
        variant_id=updated.id,
        input={"message": message},
        output={"external": external, "meta_raw": pub.get("raw")},
        reason=None,
    )

    return VariantOut.model_validate(updated)

@router.post("/{variant_id}/metrics/refresh", response_model=MetricOut)
async def refresh_variant_metrics(
    variant_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
):
    variant = await VariantsRepo.get(session, variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    if variant.status != VariantStatus.published:
        raise HTTPException(status_code=400, detail="Variant must be 'published' to refresh metrics")

    external = variant.external or {}
    post_id = external.get("post_id")
    if not post_id:
        raise HTTPException(status_code=400, detail="Variant has no external.post_id")

    provider = get_meta_provider()
    try:
        counts = await provider.fetch_post_counts(post_id=str(post_id))
    except MetaAPIError as e:
        raise HTTPException(status_code=502, detail={"message": "Meta metrics fetch failed", "meta": e.payload})

    # MVP: impressions/clicks quedan en 0 (orgánico). Luego puedes integrar insights/UTM tracking.
    impressions = 0
    clicks = 0

    likes = int(counts.get("likes", 0))
    comments = int(counts.get("comments", 0))
    shares = int(counts.get("shares", 0))

    fitness = compute_fitness(likes=likes, comments=comments, shares=shares, clicks=clicks)

    metric = await MetricsRepo.create_snapshot(
        session,
        variant_id=variant.id,
        impressions=impressions,
        likes=likes,
        comments=comments,
        shares=shares,
        clicks=clicks,
        fitness=fitness,
    )

    await LogsRepo.create(
        session,
        agent="metrics",
        campaign_id=variant.campaign_id,
        variant_id=variant.id,
        input={"post_id": str(post_id)},
        output={"counts": counts, "fitness": fitness},
        reason=None,
    )

    return MetricOut.model_validate(metric)

@router.post("/{variant_id}/unpublish", response_model=VariantOut)
async def unpublish_variant(
    variant_id: uuid.UUID,
    payload: VariantUnpublishRequest = VariantUnpublishRequest(),
    session: AsyncSession = Depends(get_db_session),
):
    variant = await VariantsRepo.get(session, variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    if variant.status != VariantStatus.published:
        raise HTTPException(status_code=400, detail="Variant must be 'published' to unpublish")

    external = variant.external or {}
    post_id = external.get("post_id")

    provider = get_meta_provider()

    meta_raw = None
    if payload.delete_remote_post:
        if not post_id:
            raise HTTPException(status_code=400, detail="Variant has no external.post_id to delete in Meta")

        try:
            resp = await provider.delete_post(post_id=str(post_id))
            meta_raw = resp.get("raw")
        except MetaAPIError as e:
            raise HTTPException(status_code=502, detail={"message": "Meta unpublish (delete) failed", "meta": e.payload})

        # Si borramos el post, limpiamos referencia
        new_external = {
            "provider": "meta",
            "post_id": None,
            "post_url": None,
            "published_at": None,
        }
    else:
        # Si NO borramos el post, dejamos post_id/post_url pero marcamos published_at=None
        # (para que el estado draft sea consistente con "no está publicado por el sistema")
        new_external = {
            "provider": external.get("provider") or "meta",
            "post_id": external.get("post_id"),
            "post_url": external.get("post_url"),
            "published_at": None,
        }

    updated = await VariantsRepo.set_status_and_external(
        session,
        variant_id=variant_id,
        status=VariantStatus.draft,
        external=new_external,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Variant not found (race condition)")

    await LogsRepo.create(
        session,
        agent="unpublish",
        campaign_id=updated.campaign_id,
        variant_id=updated.id,
        input={"post_id": str(post_id) if post_id else None, "delete_remote_post": payload.delete_remote_post},
        output={"external": new_external, "meta_raw": meta_raw},
        reason=None,
    )

    return VariantOut.model_validate(updated)