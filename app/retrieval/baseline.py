from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List, Tuple

from app.storage.queries import StoredChunk


_WORD = re.compile(r"[a-zA-Z0-9]+")


def _tokenize(s: str) -> List[str]:
    return [t.lower() for t in _WORD.findall(s)]


@dataclass(frozen=True)
class ScoredChunk:
    doc_id: str
    chunk_id: str
    page_start: int | None
    page_end: int | None
    snippet: str
    score: float


def rank_chunks(question: str, chunks: List[StoredChunk], top_k: int = 5) -> List[ScoredChunk]:
    """
    v1 baseline retrieval:
    - token overlap score normalized to 0..1-ish
    - deterministic and dependency-free
    """
    q_tokens = _tokenize(question)
    if not q_tokens:
        return []

    q_set = set(q_tokens)

    scored: List[Tuple[float, StoredChunk]] = []
    for c in chunks:
        c_tokens = _tokenize(c.text)
        if not c_tokens:
            continue
        c_set = set(c_tokens)

        overlap = len(q_set.intersection(c_set))
        # Normalize by question length with a soft cap.
        raw = overlap / max(1, len(q_set))
        score = min(1.0, raw)

        if score > 0:
            scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    out: List[ScoredChunk] = []
    for s, c in top:
        snippet = c.text.strip().replace("\n", " ")
        snippet = snippet[:240]
        out.append(
            ScoredChunk(
                doc_id=c.doc_id,
                chunk_id=c.chunk_id,
                page_start=c.page_start,
                page_end=c.page_end,
                snippet=snippet,
                score=float(s),
            )
        )
    return out
