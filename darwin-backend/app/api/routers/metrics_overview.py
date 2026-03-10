from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.api.schemas.metrics import OverviewStatsOut
from app.db.models import Campaign, Variant, VariantMetric, VariantStatus

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/overview", response_model=OverviewStatsOut)
async def metrics_overview(session: AsyncSession = Depends(get_db_session)):
    # 1) Campaign counts
    campaigns_total = await session.scalar(select(func.count(Campaign.id)))
    campaigns_total = int(campaigns_total or 0)

    # 2) Variant counts por status
    variants_published = await session.scalar(
        select(func.count(Variant.id)).where(Variant.status == VariantStatus.published)
    )
    variants_killed = await session.scalar(
        select(func.count(Variant.id)).where(Variant.status == VariantStatus.killed)
    )
    variants_published = int(variants_published or 0)
    variants_killed = int(variants_killed or 0)

    # 3) Agregados de métricas usando SOLO el último snapshot por variant
    vm = VariantMetric
    rn = func.row_number().over(partition_by=vm.variant_id, order_by=vm.computed_at.desc()).label("rn")

    latest_ranked = (
        select(
            vm.variant_id.label("variant_id"),
            vm.impressions.label("impressions"),
            vm.likes.label("likes"),
            vm.comments.label("comments"),
            vm.shares.label("shares"),
            vm.clicks.label("clicks"),
            vm.fitness.label("fitness"),
            rn,
        ).subquery()
    )

    latest_only = select(
        latest_ranked.c.impressions,
        latest_ranked.c.likes,
        latest_ranked.c.comments,
        latest_ranked.c.shares,
        latest_ranked.c.clicks,
        latest_ranked.c.fitness,
    ).where(latest_ranked.c.rn == 1).subquery()

    total_impressions = await session.scalar(select(func.coalesce(func.sum(latest_only.c.impressions), 0)))
    total_engagements = await session.scalar(
        select(
            func.coalesce(
                func.sum(
                    latest_only.c.likes
                    + latest_only.c.comments
                    + latest_only.c.shares
                    + latest_only.c.clicks
                ),
                0,
            )
        )
    )
    avg_fitness = await session.scalar(select(func.coalesce(func.avg(latest_only.c.fitness), 0.0)))

    return OverviewStatsOut(
        campaigns_total=int(total_impressions is None and campaigns_total or campaigns_total),
        variants_published=variants_published,
        variants_killed=variants_killed,
        total_impressions=int(total_impressions or 0),
        total_engagements=int(total_engagements or 0),
        avg_fitness=float(avg_fitness or 0.0),
    )