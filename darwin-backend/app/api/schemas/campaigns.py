from __future__ import annotations

import uuid
from datetime import datetime

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.schemas.metrics import MetricOut
from app.api.schemas.variants import VariantOut
from app.db.models import CampaignChannel, CampaignObjective, CampaignStatus


class CampaignProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    price_cop: int = Field(ge=0)


class CampaignCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    channel: CampaignChannel
    country: str = Field(min_length=2, max_length=2, description="ISO-3166 alpha2, ej: CO")
    product: CampaignProduct
    objective: CampaignObjective
    status: CampaignStatus = CampaignStatus.active

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        return v.upper()


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    name: str
    channel: CampaignChannel
    country: str
    product: CampaignProduct
    objective: CampaignObjective
    status: CampaignStatus
    created_at: datetime


class VariantDetailOut(VariantOut):
    latest_metric: Optional[MetricOut] = None

class CampaignDetailOut(CampaignOut):
    variants: List[VariantDetailOut]