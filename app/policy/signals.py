from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class RetrievalHit:
    doc_id: str
    chunk_id: str
    page_start: Optional[int]
    page_end: Optional[int]
    snippet: str
    score: float  # normalized 0..1


@dataclass(frozen=True)
class RetrievalSignals:
    question: str
    hits: List[RetrievalHit]

    # Optional convenience fields a retriever may precompute
    top1_score: Optional[float] = None
    topk_gap: Optional[float] = None
