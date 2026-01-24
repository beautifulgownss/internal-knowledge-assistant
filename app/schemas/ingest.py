from __future__ import annotations

from typing import List, Literal
from pydantic import BaseModel, Field


class LocalFolderSource(BaseModel):
    type: Literal["local_folder"] = "local_folder"
    path: str = Field(..., min_length=1, description="Path to folder containing PDFs")


class IngestRequest(BaseModel):
    collection_id: str = Field(..., min_length=1)
    source: LocalFolderSource
    rebuild_index: bool = Field(default=False, description="If true, rebuild the collection index from scratch")


class FailedDoc(BaseModel):
    doc_id: str
    reason: str


class IngestResponse(BaseModel):
    trace_id: str
    collection_id: str
    ingested_docs: int = Field(..., ge=0)
    chunks_created: int = Field(..., ge=0)
    failed_docs: List[FailedDoc] = Field(default_factory=list)
