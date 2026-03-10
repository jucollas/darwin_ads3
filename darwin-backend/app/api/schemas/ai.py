from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LLMVariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: str = Field(min_length=1, max_length=120)
    primary_text: str = Field(min_length=1, max_length=2000)
    cta: str = Field(min_length=1, max_length=50)
    image_prompt: str = Field(min_length=1, max_length=1000)
    image_url: str | None = None


class VariantPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["variant_pack"] = "variant_pack"
    version: Literal["1.0"] = "1.0"
    variants: list[LLMVariant] = Field(min_length=3, max_length=3)
    warnings: list[str] = Field(default_factory=list)


class GenerateVariantsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_prompt: str = Field(min_length=1, max_length=2000)