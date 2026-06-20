from __future__ import annotations

from typing import List

from app.policy.signals import RetrievalHit
from app.schemas.common import PolicyAction


def generate_answer(question: str, hits: List[RetrievalHit], policy_action: PolicyAction) -> str:
    """
    Mocks what an LLM would return when synthesizing an answer from
    retrieved chunks. In a later phase this is replaced with a real
    generation API call, grounded strictly in the provided hits.

    Only called for answer_with_warning and answer policy actions.
    refuse and ask_clarifying are handled upstream and never reach here.
    """
    if not hits:
        return "No supporting evidence was available to generate an answer."

    top_hit = hits[0]
    supporting_snippets = [h.snippet for h in hits[:3]]

    answer_lines = [
        f"Based on {top_hit.doc_id} (page {top_hit.page_start}), {top_hit.snippet}"
    ]

    if len(supporting_snippets) > 1:
        additional = " ".join(supporting_snippets[1:])
        answer_lines.append(f"Additional context: {additional}")

    if policy_action == PolicyAction.answer_with_warning:
        answer_lines.append(
            "Note: this answer is based on partial or moderately confident evidence. "
            "Please verify against the cited sources."
        )

    return " ".join(answer_lines)