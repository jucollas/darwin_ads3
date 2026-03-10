from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import VariantStatus

class VariantUnpublishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    delete_remote_post: bool = Field(default=True, description="Si true, borra el post en Meta")


class VariantCreative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: str = Field(min_length=1, max_length=120)
    primary_text: str = Field(min_length=1, max_length=2000)
    cta: str = Field(min_length=1, max_length=50)
    image_prompt: str = Field(min_length=1, max_length=1000)
    image_url: Optional[str] = None


class VariantExternal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Optional[str] = None     # "meta"
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    published_at: Optional[datetime] = None


class VariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    generation: int
    parent_variant_id: Optional[uuid.UUID] = None
    status: VariantStatus
    creative: VariantCreative
    external: VariantExternal
    created_at: datetime