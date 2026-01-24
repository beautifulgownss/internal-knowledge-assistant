from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.storage.db import connect, init_schema


@dataclass(frozen=True)
class StoredChunk:
    doc_id: str
    chunk_id: str
    page_start: Optional[int]
    page_end: Optional[int]
    text: str


def get_collection_stats(collection_id: str) -> dict:
    conn = connect()
    init_schema(conn)

    doc_count = conn.execute(
        "SELECT COUNT(*) AS c FROM documents WHERE collection_id = ?",
        (collection_id,),
    ).fetchone()["c"]

    chunk_count = conn.execute(
        "SELECT COUNT(*) AS c FROM chunks WHERE collection_id = ?",
        (collection_id,),
    ).fetchone()["c"]

    last_run = conn.execute(
        """
        SELECT created_at, ingested_docs, chunks_created, failed_docs
        FROM ingest_runs
        WHERE collection_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (collection_id,),
    ).fetchone()

    conn.close()

    return {
        "collection_id": collection_id,
        "documents": int(doc_count),
        "chunks": int(chunk_count),
        "last_ingest": dict(last_run) if last_run else None,
    }


def fetch_candidate_chunks(collection_id: str, limit: int = 25) -> List[StoredChunk]:
    """
    v1 retrieval baseline: fetch recent chunks (no embeddings yet).
    We'll score them with a simple lexical heuristic in the API layer.
    """
    conn = connect()
    init_schema(conn)

    rows = conn.execute(
        """
        SELECT doc_id, chunk_id, page_start, page_end, text
        FROM chunks
        WHERE collection_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (collection_id, limit),
    ).fetchall()

    conn.close()
    return [
        StoredChunk(
            doc_id=r["doc_id"],
            chunk_id=r["chunk_id"],
            page_start=r["page_start"],
            page_end=r["page_end"],
            text=r["text"],
        )
        for r in rows
    ]
