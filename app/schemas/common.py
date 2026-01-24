from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class PolicyAction(str, Enum):
    answer = "answer"
    answer_with_warning = "answer_with_warning"
    ask_clarifying = "ask_clarifying"
    refuse = "refuse"
    return_sources = "return_sources"


class SourceType(str, Enum):
    pdf = "pdf"


class TraceEnvelope(BaseModel):
    trace_id: str = Field(..., description="Trace ID for correlating logs and debugging")


class Citation(BaseModel):
    doc_id: str = Field(..., description="Stable document identifier, usually filename")
    source_type: SourceType = Field(default=SourceType.pdf)
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    chunk_id: str = Field(..., description="Chunk identifier within a document")
    snippet: str = Field(..., description="Short excerpt shown to the user")
    score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Retrieval score if available"
    )
