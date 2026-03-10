from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.api.schemas.ai import VariantPack

import json


load_dotenv()


def _require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"{name} no está definido en el entorno")
    return v


OPENAI_API_KEY = _require("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


def _variant_pack_schema(n: int = 3) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["variant_pack"]},
            "version": {"type": "string", "enum": ["1.0"]},
            "variants": {
                "type": "array",
                "minItems": n,
                "maxItems": n,
                "items": {
                    "type": "object",
                    "properties": {
                        "headline": {"type": "string"},
                        "primary_text": {"type": "string"},
                        "cta": {"type": "string"},
                        "image_prompt": {"type": "string"},
                        "image_url": {"type": ["string", "null"]},
                    },
                    # 🔥 OpenAI exige que required incluya TODAS las keys de properties
                    "required": ["headline", "primary_text", "cta", "image_prompt", "image_url"],
                    "additionalProperties": False,
                },
            },
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["type", "version", "variants", "warnings"],
        "additionalProperties": False,
    }


async def generate_variant_pack(*, campaign_context: dict[str, Any], user_prompt: str) -> VariantPack:
    system_msg = (
        "Eres un asistente de marketing. Genera 3 variantes de anuncio (copy) para la campaña. "
        "Respeta el contexto: producto, precio, país, canal y objetivo. "
        "No inventes datos sensibles ni promesas falsas. Devuelve SOLO el JSON requerido."
    )

    user_msg = {
        "campaign_context": campaign_context,
        "user_prompt": user_prompt,
        "requirements": {
            "n_variants": 3,
            "language": "es",
            "keep_it_concise": True,
        },
    }

    resp = await client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": [{"type": "input_text", "text": json.dumps(user_msg, ensure_ascii=False)}]},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "variant_pack",
                "schema": _variant_pack_schema(3),
                "strict": True,
            }
        },
        temperature=0.7,
    )
    # En structured outputs, response.output_text debe ser JSON válido según schema. :contentReference[oaicite:1]{index=1}
    return VariantPack.model_validate_json(resp.output_text)