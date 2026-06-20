# Internal Knowledge Assistant

A production-style internal assistant that answers questions from PDF documents with citations and explicit confidence handling.

This is built for a single organization, not as a multi-tenant product. It prioritizes clear contracts, predictable behavior, and defensive design over novelty or scale. It is not a chat interface. It is an internal service meant to be consumed by other systems or tools.

## What it actually does right now

This isn't a contracts-only skeleton. The full loop is real and runs end to end:

1. **Ingests PDFs** into logical collections (e.g. `handbook`, `policies`), parsing and chunking real documents, not mocked content
2. **Retrieves** candidate chunks from SQLite and ranks them lexically against the question
3. **Decides**, via a policy engine, whether the retrieved evidence is strong enough to answer, ambiguous enough to ask a clarifying question, or weak enough to refuse outright
4. **Generates** an answer grounded in the retrieved chunks, with a confidence-appropriate warning attached when evidence is only moderate
5. **Returns citations** with page-level references for every claim, traceable back to the exact source document and chunk

Every request gets a trace ID. Every answer comes with its supporting evidence attached, not asserted separately.

## The policy engine

This is the part that makes the system trustworthy instead of just functional. Given retrieval signals (top score, score gap between top results), it picks one of four actions:

| Evidence quality | Action | What happens |
|---|---|---|
| None or very weak | `refuse` | Returns a refusal, zero citations, no generation call |
| Ambiguous (close scores, no clear winner) | `ask_clarifying` | Returns a clarifying question instead of guessing |
| Moderate | `answer_with_warning` | Generates an answer, attaches a verification warning |
| Strong | `answer` | Generates an answer with full confidence |

Generation only runs for the last two. `refuse` and `ask_clarifying` never reach the generation step, there's nothing to ground an answer in, so nothing gets generated.

## Generation, mocked for now

The generation step is currently mocked, same pattern used across other projects in this portfolio: a function with the exact signature and behavior a real LLM call will need, so the contract gets nailed down before any API key or cost is involved. It takes the question, the ranked retrieval hits, and the policy decision, and produces an answer that's actually grounded in the retrieved snippets, not a placeholder string.

This was verified against both real code paths during development: a PTO question against an ingested handbook returned a real citation-backed answer with the correct moderate-confidence warning attached, and a nonsense question correctly triggered `refuse` with zero citations and no generation call at all.

## What this system does not do

- It does not claim to be multi-tenant or internet-facing
- It does not include authentication or access control (out of scope for v1)
- It does not attempt to answer questions without supporting documents
- It does not hide uncertainty or fabricate answers

These constraints are deliberate and reflect real internal tooling tradeoffs, not gaps that got missed.

## Architecture

```
PDF documents
        ↓
app/ingest/pdf_ingest.py     → parses and chunks PDFs into a collection
app/ingest/runner.py         → orchestrates the ingestion job, tracks failures
        ↓
app/storage/db.py            → SQLite storage for chunks and collection metadata
app/storage/queries.py       → fetches candidate chunks for a given collection
        ↓
app/retrieval/baseline.py    → lexical ranking of candidates against the question
        ↓
app/policy/signals.py        → packages retrieval scores into a decision input
app/policy/engine.py         → decides refuse / clarify / answer / answer_with_warning
        ↓
app/generation/__init__.py   → generates a grounded answer (mocked, real-call-shaped)
        ↓
app/main.py                  → FastAPI routes: /v1/ask, /v1/ingest, /v1/health, /v1/collections/{id}/stats
```

Each layer has one job. Retrieval doesn't know about policy. Policy doesn't know about generation. Generation never runs without a policy decision authorizing it. That separation is what makes this auditable, you can trace exactly which layer produced which part of the final answer.

## Design goals

- Reliability over cleverness
- Explicit failure modes, not silent ones
- Auditable outputs with citations
- Clear separation between ingestion, retrieval, policy, and generation
- Reproducible local development

## Tech stack

- **FastAPI + Pydantic** for a versioned, schema-validated API
- **SQLite** for chunk storage, no external vector DB dependency for the v1 lexical baseline
- **pypdf** for PDF parsing and ingestion
- **Mocked generation**, structured to be a drop-in swap for a real Anthropic/OpenAI call later

## Quick start

```bash
make venv
make install
make run
```

Health check:

```bash
make health
```

Ask a question against an ingested collection:

```bash
make ask
```

This runs a real request through the full loop, retrieval, policy decision, and generation, against whatever's been ingested into the `handbook` collection.

## Key engineering decisions

**Policy decides before generation runs, not after.** The system never generates an answer and then decides whether to show it. It decides first, based on retrieval signal strength alone, whether generation should even be attempted. This is what prevents the system from confidently answering questions it has no real basis to answer.

**Generation is mocked but contract-real.** The mock function takes exactly what a real LLM call would need (question, ranked hits, policy action) and returns exactly what the API contract expects. Swapping in a real model later is a function-body change, not an architecture change.

**Citations are a byproduct of retrieval, not an afterthought.** Every hit that informed a decision gets returned as a citation, whether or not generation ran. Even a `refuse` response is auditable, you can see exactly what evidence (or lack of it) led to the refusal.

**Lexical ranking before vector search.** The v1 retrieval baseline ranks chunks lexically against the question rather than reaching for embeddings and a vector DB immediately. This keeps the dependency footprint small and the ranking logic transparent while the rest of the system (policy, generation, citations) gets proven out first.

## What's next

- [ ] Swap mocked generation for a real Anthropic/OpenAI call, same input/output contract
- [ ] Add a real eval set (golden question/answer/citation triples) to measure generation quality and catch regressions
- [ ] Add embedding-based retrieval as an option alongside the lexical baseline
- [ ] Add authentication and access control once this moves beyond v1 single-org scope
- [ ] Expand ingestion to handle more document types beyond PDF
