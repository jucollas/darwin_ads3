from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    message: str
    status_code: int
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorEnvelope