from __future__ import annotations

import uuid
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class DarwinRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    threshold_up: float = Field(default=5.0, description="fitness >= threshold_up => duplicate")
    threshold_down: float = Field(default=-3.0, description="fitness <= threshold_down => kill")
    dry_run: bool = Field(default=False, description="si true, no escribe cambios")
    delete_remote_post: bool = Field(default=True, description="si true, intenta borrar post en Meta al matar")


class DarwinDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: uuid.UUID
    action: Literal["duplicate", "kill", "skip"]
    fitness: Optional[float] = None
    reason: str
    child_variant_id: Optional[uuid.UUID] = None
    meta_delete_success: Optional[bool] = None
    meta_delete_error: Optional[dict] = None


class DarwinRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    processed: int
    duplicated: int
    killed: int
    skipped: int
    decisions: list[DarwinDecision]