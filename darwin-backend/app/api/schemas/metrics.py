from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    variant_id: uuid.UUID
    impressions: int = Field(ge=0)
    likes: int = Field(ge=0)
    comments: int = Field(ge=0)
    shares: int = Field(ge=0)
    clicks: int = Field(ge=0)
    fitness: float
    computed_at: datetime

class OverviewStatsOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    campaigns_total: int = Field(ge=0)
    variants_published: int = Field(ge=0)
    variants_killed: int = Field(ge=0)
    total_impressions: int = Field(ge=0)
    total_engagements: int = Field(ge=0)
    avg_fitness: float