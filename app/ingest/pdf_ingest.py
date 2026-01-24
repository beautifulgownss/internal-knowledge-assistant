from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedPage:
    doc_id: str
    source_path: str
    page_number: int  # 1-indexed
    text: str


def extract_pages(pdf_path: Path) -> Tuple[str, int, List[ExtractedPage]]:
    """
    Extract text per page from a PDF.
    Returns (doc_id, page_count, pages).
    """
    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)
    doc_id = pdf_path.name

    pages: List[ExtractedPage] = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        pages.append(
            ExtractedPage(
                doc_id=doc_id,
                source_path=str(pdf_path),
                page_number=i,
                text=text,
            )
        )

    return doc_id, page_count, pages


def chunk_pages(
    pages: List[ExtractedPage],
    max_chars: int = 1200,
    overlap_chars: int = 150,
) -> Iterable[dict]:
    """
    Deterministic chunking over concatenated page text.
    Produces chunks with page_start/page_end metadata.

    v1: character-based splitting (simple and inspectable).
    """
    # Build a single concatenated string with page boundaries.
    joined_parts: List[Tuple[int, str]] = []
    for p in pages:
        if p.text:
            joined_parts.append((p.page_number, p.text))

    if not joined_parts:
        return []

    # Concatenate with separators while tracking page offsets.
    # We will chunk over the combined text but keep approximate page ranges.
    separator = "\n\n"
    combined = ""
    page_spans: List[Tuple[int, int, int]] = []  # (page_number, start_idx, end_idx)
    for page_number, text in joined_parts:
        start = len(combined)
        combined += text + separator
        end = len(combined)
        page_spans.append((page_number, start, end))

    chunks = []
    idx = 0
    chunk_num = 0
    n = len(combined)

    while idx < n:
        chunk_num += 1
        end = min(idx + max_chars, n)
        chunk_text = combined[idx:end].strip()
        if not chunk_text:
            break

        # Determine page_start/page_end by span overlap.
        page_numbers = []
        for page_number, s, e in page_spans:
            if e <= idx:
                continue
            if s >= end:
                break
            page_numbers.append(page_number)

        page_start: Optional[int] = min(page_numbers) if page_numbers else None
        page_end: Optional[int] = max(page_numbers) if page_numbers else None

        chunks.append(
            {
                "chunk_id": f"c{chunk_num:05d}",
                "page_start": page_start,
                "page_end": page_end,
                "text": chunk_text,
            }
        )

        if end == n:
            break
        idx = max(0, end - overlap_chars)

    return chunks
