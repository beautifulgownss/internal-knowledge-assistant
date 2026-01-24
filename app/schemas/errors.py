from __future__ import annotations

from typing import Any, Dict
from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(..., description="Stable error code for clients")
    message: str = Field(..., description="Human readable summary")
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    trace_id: str
    error: ErrorBody
