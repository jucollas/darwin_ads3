from __future__ import annotations

import copy
import hashlib
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.darwin import DarwinDecision, DarwinRunRequest, DarwinRunResult
from app.db.models import VariantStatus
from app.db.repos.logs_repo import LogsRepo
from app.db.repos.metrics_repo import MetricsRepo
from app.db.repos.variants_repo import VariantsRepo
from app.services.providers.meta_provider import MetaAPIError, get_meta_provider


def _stable_pick(variant_id: uuid.UUID, options: list[str]) -> str:
    h = hashlib.sha256(str(variant_id).encode("utf-8")).hexdigest()
    idx = int(h[:8], 16) % len(options)
    return options[idx]


def mutate_creative(creative: dict[str, Any], *, parent_id: uuid.UUID) -> dict[str, Any]:
    """
    Mutación simple y demostrable (sin LLM):
    - headline: añade un “gancho” alterno
    - primary_text: cambia la primera línea con un lead alterno
    - mantiene CTA e image_prompt
    """
    c = copy.deepcopy(creative) if creative else {}
    headline = (c.get("headline") or "").strip()
    primary = (c.get("primary_text") or "").strip()

    hooks = ["🔥", "⚡", "✨", "🍔", "✅"]
    leadins = [
        "¡Hoy es el día!",
        "Promo por tiempo limitado:",
        "Antojo resuelto:",
        "Atención Cali:",
        "Solo por hoy:",
    ]

    hook = _stable_pick(parent_id, hooks)
    lead = _stable_pick(parent_id, leadins)

    if headline:
        c["headline"] = f"{hook} {headline}"
    else:
        c["headline"] = f"{hook} Nueva promo"

    if primary:
        # reemplaza/inyecta primera línea
        lines = primary.splitlines()
        if lines:
            lines[0] = f"{lead} {lines[0]}"
            c["primary_text"] = "\n".join(lines).strip()
        else:
            c["primary_text"] = f"{lead} {primary}".strip()
    else:
        c["primary_text"] = lead

    # asegurar keys mínimas
    c.setdefault("cta", "Enviar mensaje")
    c.setdefault("image_prompt", "Banner publicitario moderno")
    c.setdefault("image_url", None)

    return c


async def run_darwin(session: AsyncSession, req: DarwinRunRequest) -> DarwinRunResult:
    published = await VariantsRepo.list_by_status(session, status=VariantStatus.published, limit=500, offset=0)

    decisions: list[DarwinDecision] = []
    duplicated = 0
    killed = 0
    skipped = 0

    meta = get_meta_provider()

    for v in published:
        latest = await MetricsRepo.latest_for_variant(session, v.id)
        if not latest:
            skipped += 1
            decisions.append(
                DarwinDecision(
                    variant_id=v.id,
                    action="skip",
                    fitness=None,
                    reason="no_metrics",
                )
            )
            continue

        fitness = float(latest.fitness)

        # DUPLICATE
        if fitness >= req.threshold_up:
            if req.dry_run:
                duplicated += 1
                decisions.append(
                    DarwinDecision(
                        variant_id=v.id,
                        action="duplicate",
                        fitness=fitness,
                        reason="dry_run_duplicate",
                        child_variant_id=None,
                    )
                )
                continue

            child_creative = mutate_creative(v.creative, parent_id=v.id)
            child_external = {"provider": "meta", "post_id": None, "post_url": None, "published_at": None}

            child = await VariantsRepo.create(
                session,
                campaign_id=v.campaign_id,
                creative=child_creative,
                external=child_external,
                generation=int(v.generation) + 1,
                parent_variant_id=v.id,
                status=VariantStatus.draft,
            )

            duplicated += 1

            await LogsRepo.create(
                session,
                agent="darwin",
                campaign_id=v.campaign_id,
                variant_id=v.id,
                input={"fitness": fitness, "threshold_up": req.threshold_up, "threshold_down": req.threshold_down},
                output={"action": "duplicate", "child_variant_id": str(child.id)},
                reason="fitness>=threshold_up",
            )

            decisions.append(
                DarwinDecision(
                    variant_id=v.id,
                    action="duplicate",
                    fitness=fitness,
                    reason="fitness>=threshold_up",
                    child_variant_id=child.id,
                )
            )
            continue

        # KILL
        if fitness <= req.threshold_down:
            meta_success = None
            meta_error = None

            post_id = (v.external or {}).get("post_id")

            if req.delete_remote_post and post_id:
                try:
                    if not req.dry_run:
                        await meta.delete_post(post_id=str(post_id))
                    meta_success = True
                except MetaAPIError as e:
                    meta_success = False
                    meta_error = {"status_code": e.status_code, "payload": e.payload}

            if not req.dry_run:
                await VariantsRepo.update_status(session, variant_id=v.id, status=VariantStatus.killed)

            killed += 1

            await LogsRepo.create(
                session,
                agent="darwin",
                campaign_id=v.campaign_id,
                variant_id=v.id,
                input={
                    "fitness": fitness,
                    "threshold_up": req.threshold_up,
                    "threshold_down": req.threshold_down,
                    "delete_remote_post": req.delete_remote_post,
                    "post_id": str(post_id) if post_id else None,
                    "dry_run": req.dry_run,
                },
                output={
                    "action": "kill",
                    "meta_delete_success": meta_success,
                    "meta_delete_error": meta_error,
                },
                reason="fitness<=threshold_down",
            )

            decisions.append(
                DarwinDecision(
                    variant_id=v.id,
                    action="kill",
                    fitness=fitness,
                    reason="fitness<=threshold_down",
                    meta_delete_success=meta_success,
                    meta_delete_error=meta_error,
                )
            )
            continue

        # SKIP (neutral zone)
        skipped += 1
        decisions.append(
            DarwinDecision(
                variant_id=v.id,
                action="skip",
                fitness=fitness,
                reason="neutral_fitness",
            )
        )

    return DarwinRunResult(
        processed=len(published),
        duplicated=duplicated,
        killed=killed,
        skipped=skipped,
        decisions=decisions,
    )