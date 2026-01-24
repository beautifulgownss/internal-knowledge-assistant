from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from app.ingest.pdf_ingest import extract_pages, chunk_pages
from app.storage.db import connect, init_schema


@dataclass(frozen=True)
class FailedDocInfo:
    doc_id: str
    reason: str


@dataclass(frozen=True)
class IngestResult:
    ingested_docs: int
    chunks_created: int
    failed: List[FailedDocInfo]


def ingest_pdf_folder(collection_id: str, folder_path: str, trace_id: str, rebuild: bool = False) -> IngestResult:
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        return IngestResult(ingested_docs=0, chunks_created=0, failed=[FailedDocInfo(doc_id="", reason="folder_not_found")])

    conn = connect()
    init_schema(conn)

    if rebuild:
        conn.execute("DELETE FROM chunks WHERE collection_id = ?", (collection_id,))
        conn.execute("DELETE FROM documents WHERE collection_id = ?", (collection_id,))
        conn.commit()

    pdf_files = sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"])

    ingested_docs = 0
    chunks_created = 0
    failed: List[FailedDocInfo] = []

    for pdf_path in pdf_files:
        try:
            doc_id, page_count, pages = extract_pages(pdf_path)

            # Insert document row
            conn.execute(
                """
                INSERT OR REPLACE INTO documents (collection_id, doc_id, source_path, page_count)
                VALUES (?, ?, ?, ?)
                """,
                (collection_id, doc_id, str(pdf_path), page_count),
            )

            chunks = list(chunk_pages(pages))
            for c in chunks:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO chunks (collection_id, doc_id, chunk_id, page_start, page_end, text)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        collection_id,
                        doc_id,
                        c["chunk_id"],
                        c["page_start"],
                        c["page_end"],
                        c["text"],
                    ),
                )

            conn.commit()
            ingested_docs += 1
            chunks_created += len(chunks)

        except Exception as e:
            failed.append(FailedDocInfo(doc_id=pdf_path.name, reason=f"pdf_ingest_failed:{type(e).__name__}"))
            continue

    conn.execute(
        """
        INSERT INTO ingest_runs (trace_id, collection_id, source_path, ingested_docs, chunks_created, failed_docs)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (trace_id, collection_id, folder_path, ingested_docs, chunks_created, len(failed)),
    )
    conn.commit()
    conn.close()

    return IngestResult(ingested_docs=ingested_docs, chunks_created=chunks_created, failed=failed)
