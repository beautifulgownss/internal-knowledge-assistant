from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.policy.signals import RetrievalSignals
from app.schemas.common import ConfidenceLevel, PolicyAction


@dataclass(frozen=True)
class PolicyDecision:
    confidence: ConfidenceLevel
    action: PolicyAction
    warnings: List[str]
    clarifying_question: str | None = None


def _calc_top1_score(signals: RetrievalSignals) -> float:
    if signals.top1_score is not None:
        return signals.top1_score
    if not signals.hits:
        return 0.0
    return max(h.score for h in signals.hits)


def _calc_topk_gap(signals: RetrievalSignals, k: int = 5) -> float:
    if signals.topk_gap is not None:
        return signals.topk_gap
    scores = sorted((h.score for h in signals.hits), reverse=True)
    if not scores:
        return 0.0
    top1 = scores[0]
    topk = scores[min(k - 1, len(scores) - 1)]
    return top1 - topk


def decide(signals: RetrievalSignals) -> PolicyDecision:
    """
    v1 policy engine.

    Rules:
    - No or very weak evidence -> refuse
    - Ambiguous evidence -> ask clarifying question
    - Moderate evidence -> answer with warning
    - Strong evidence -> answer
    """

    top1 = _calc_top1_score(signals)
    gap = _calc_topk_gap(signals)

    STRONG_TOP1 = 0.55
    MODERATE_TOP1 = 0.35
    WEAK_TOP1 = 0.20
    AMBIGUOUS_GAP = 0.06

    if not signals.hits or top1 < WEAK_TOP1:
        return PolicyDecision(
            confidence=ConfidenceLevel.low,
            action=PolicyAction.refuse,
            warnings=["Insufficient supporting evidence in the selected collection."],
        )
    if len(signals.hits) >= 2 and gap < AMBIGUOUS_GAP:
        return PolicyDecision(
            confidence=ConfidenceLevel.low,
            action=PolicyAction.ask_clarifying,
            warnings=["Question appears ambiguous relative to retrieved evidence."],
            clarifying_question="Can you clarify what specific topic or section you mean?",
        )

    if top1 < STRONG_TOP1:
        return PolicyDecision(
            confidence=ConfidenceLevel.medium,
            action=PolicyAction.answer_with_warning,
            warnings=["Answer may be incomplete. Verify citations."],
        )

    return PolicyDecision(
        confidence=ConfidenceLevel.high,
        action=PolicyAction.answer,
        warnings=[],
    )
