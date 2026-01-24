from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field

from .common import Citation, ConfidenceLevel, PolicyAction


class AskRequest(BaseModel):
    collection_id: str = Field(..., min_length=1, description="Logical namespace for a document set")
    question: str = Field(..., min_length=1, description="User question")
    top_k: int = Field(default=5, ge=1, le=20, description="How many chunks to retrieve before policy checks")
    max_context_chunks: int = Field(default=6, ge=1, le=20, description="Max chunks passed into generation")


class AskResponse(BaseModel):
    trace_id: str
    collection_id: str
    question: str
    answer: str = Field(..., description="Answer or clarifying question depending on policy_action")
    citations: List[Citation] = Field(default_factory=list)
    confidence: ConfidenceLevel
    policy_action: PolicyAction
    warnings: List[str] = Field(default_factory=list)
