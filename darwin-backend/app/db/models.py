from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SAEnum
from sqlalchemy import Boolean


# ---------- Base ----------
class Base(DeclarativeBase):
    pass


# ---------- Enums (mínimos del MVP) ----------
class CampaignChannel(str, Enum):
    facebook_page = "facebook_page"
    instagram_business = "instagram_business"


class CampaignObjective(str, Enum):
    engagement = "engagement"
    traffic = "traffic"


class CampaignStatus(str, Enum):
    active = "active"
    paused = "paused"
    archived = "archived"


class VariantStatus(str, Enum):
    draft = "draft"
    published = "published"
    killed = "killed"


# ---------- Opcionales (para no rehacer luego) ----------
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="user")


class Integration(Base):
    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    provider: Mapped[str] = mapped_column(String(50))  # "meta"
    access_token: Mapped[str] = mapped_column(Text)    # luego: encrypt
    page_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ig_biz_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ---------- Core MVP ----------
class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(200))
    channel: Mapped[CampaignChannel] = mapped_column(
        SAEnum(CampaignChannel, name="campaign_channel"), nullable=False
    )
    country: Mapped[str] = mapped_column(String(2), nullable=False)  # "CO"
    product: Mapped[dict] = mapped_column(JSONB, nullable=False)     # {"name":..., "price_cop":...}
    objective: Mapped[CampaignObjective] = mapped_column(
        SAEnum(CampaignObjective, name="campaign_objective"), nullable=False
    )
    status: Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus, name="campaign_status"), nullable=False, server_default="active"
    )

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User | None"] = relationship(back_populates="campaigns")
    variants: Mapped[list["Variant"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan", passive_deletes=True
    )


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )

    generation: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("variants.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[VariantStatus] = mapped_column(
        SAEnum(VariantStatus, name="variant_status"), nullable=False, server_default="draft"
    )

    creative: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )  # {"headline","primary_text","cta","image_prompt","image_url"}

    external: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )  # {"provider","post_id","post_url","published_at"}

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    campaign: Mapped["Campaign"] = relationship(back_populates="variants")

    parent: Mapped["Variant | None"] = relationship(
        remote_side="Variant.id", back_populates="children", uselist=False
    )
    children: Mapped[list["Variant"]] = relationship(back_populates="parent")

    metrics: Mapped[list["VariantMetric"]] = relationship(
        back_populates="variant", cascade="all, delete-orphan", passive_deletes=True
    )


class VariantMetric(Base):
    __tablename__ = "variant_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("variants.id", ondelete="CASCADE"), nullable=False
    )

    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shares: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    fitness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    computed_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    variant: Mapped["Variant"] = relationship(back_populates="metrics")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("variants.id", ondelete="SET NULL"), nullable=True
    )

    agent: Mapped[str] = mapped_column(String(50), nullable=False)  # create|duplicate|delete|publish|metrics|darwin
    input: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

class SchedulerSettings(Base):
    __tablename__ = "scheduler_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default="120")
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ---------- Índices útiles para performance ----------
Index("ix_variants_campaign_id", Variant.campaign_id)
Index("ix_variants_status", Variant.status)
Index("ix_variant_metrics_variant_id", VariantMetric.variant_id)
Index("ix_variant_metrics_computed_at", VariantMetric.computed_at)
Index("ix_agent_logs_created_at", AgentLog.created_at)

