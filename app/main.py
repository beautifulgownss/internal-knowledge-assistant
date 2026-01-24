from __future__ import annotations

import uuid
from fastapi import FastAPI

from app.policy.engine import decide
from app.policy.signals import RetrievalHit, RetrievalSignals
from app.schemas.ask import AskRequest, AskResponse
from app.schemas.ingest import IngestRequest, IngestResponse
from app.ingest.runner import ingest_pdf_folder
from app.schemas.common import PolicyAction
from app.storage.queries import fetch_candidate_chunks, get_collection_stats
from app.retrieval.baseline import rank_chunks

APP_VERSION = "0.1.0"

app = FastAPI(
    title="Internal Knowledge Assistant",
    version=APP_VERSION,
)


def new_trace_id() -> str:
    return str(uuid.uuid4())


@app.get("/v1/health")
def health():
    return {"status": "ok", "service": "internal-knowledge-assistant", "version": APP_VERSION}


def _simulate_retrieval(question: str):
    """
    Simulated retrieval for Session 2.
    This lets us validate policy behavior without PDF parsing or vector search.
    """
    q = question.lower().strip()

    # Very weak evidence scenario
    if "asdf" in q or "nonsense" in q:
        return []

    # Strong scenario (specific beats generic)
    if "pto" in q or "vacation" in q:
        return [
            RetrievalHit("handbook.pdf", "p12_c2", 12, 12, "PTO accrual and usage rules.", 0.86),
            RetrievalHit("handbook.pdf", "p13_c1", 13, 13, "Requesting PTO and approval workflow.", 0.80),
            RetrievalHit("handbook.pdf", "p12_c3", 12, 12, "Carryover and payout rules.", 0.79),
            RetrievalHit("handbook.pdf", "p14_c1", 14, 14, "Holidays and company shutdown days.", 0.74),
            RetrievalHit("handbook.pdf", "p11_c2", 11, 11, "Timekeeping and attendance policy.", 0.71),
        ]

    # Ambiguous scenario (generic policy questions)
    if "policy" in q:
        return [
            RetrievalHit("handbook.pdf", "p3_c1", 3, 3, "Policies overview and general guidance.", 0.66),
            RetrievalHit("handbook.pdf", "p7_c2", 7, 7, "Policy exceptions and approvals.", 0.64),
            RetrievalHit("policies.pdf", "p2_c1", 2, 2, "Policy definitions and scope.", 0.63),
            RetrievalHit("policies.pdf", "p5_c3", 5, 5, "Policy enforcement details.", 0.62),
            RetrievalHit("handbook.pdf", "p4_c2", 4, 4, "Related policies and references.", 0.61),
        ]

    # Moderate scenario
    return [
        RetrievalHit("handbook.pdf", "p6_c1", 6, 6, "General guidance related to the topic.", 0.68),
        RetrievalHit("handbook.pdf", "p6_c2", 6, 6, "Additional details that may be relevant.", 0.61),
        RetrievalHit("handbook.pdf", "p9_c1", 9, 9, "A related section with partial coverage.", 0.59),
    ]


@app.post("/v1/ask", response_model=AskResponse)
def ask(req: AskRequest):
    trace_id = new_trace_id()

    # v1 real retrieval baseline: pull stored chunks from SQLite and rank lexically.
    candidates = fetch_candidate_chunks(collection_id=req.collection_id, limit=50)
    ranked = rank_chunks(req.question, candidates, top_k=req.top_k)

    # Convert scored chunks into policy retrieval signals
    hits = [
        RetrievalHit(
            doc_id=sc.doc_id,
            chunk_id=sc.chunk_id,
            page_start=sc.page_start,
            page_end=sc.page_end,
            snippet=sc.snippet,
            score=sc.score,
        )
        for sc in ranked
    ]

    signals = RetrievalSignals(question=req.question, hits=hits)
    decision = decide(signals)

    # Generation is still stubbed. We return policy-based responses with real citations.
    if decision.action == PolicyAction.ask_clarifying:
        answer_text = decision.clarifying_question or "Can you clarify your question?"
    elif decision.action == PolicyAction.refuse:
        answer_text = "I can't answer confidently from the current documents in this collection."
    else:
        answer_text = "Contract-only response. Retrieval is real, generation is not enabled yet."

    return AskResponse(
        trace_id=trace_id,
        collection_id=req.collection_id,
        question=req.question,
        answer=answer_text,
        citations=[
            {
                "doc_id": h.doc_id,
                "source_type": "pdf",
                "page_start": h.page_start,
                "page_end": h.page_end,
                "chunk_id": h.chunk_id,
                "snippet": h.snippet,
                "score": h.score,
            }
            for h in hits
        ],
        confidence=decision.confidence,
        policy_action=decision.action,
        warnings=decision.warnings,
    )


@app.post("/v1/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest):
    trace_id = new_trace_id()

    result = ingest_pdf_folder(
        collection_id=req.collection_id,
        folder_path=req.source.path,
        trace_id=trace_id,
        rebuild=req.rebuild_index,
    )

    return IngestResponse(
        trace_id=trace_id,
        collection_id=req.collection_id,
        ingested_docs=result.ingested_docs,
        chunks_created=result.chunks_created,
        failed_docs=[{"doc_id": f.doc_id, "reason": f.reason} for f in result.failed],
    )


@app.get("/v1/collections/{collection_id}/stats")
def collection_stats(collection_id: str):
    return get_collection_stats(collection_id)
