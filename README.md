# Internal Knowledge Assistant

A production-style internal assistant that answers questions from PDF documents with citations and explicit confidence handling.

This project is intentionally scoped to demonstrate how to build a reliable, auditable AI application for a single organization. It prioritizes clear contracts, predictable behavior, and defensive design over novelty or scale.

## What this system does

- Ingests PDF documents into logical collections (for example: `handbook`, `policies`)
- Answers user questions using retrieval-augmented generation
- Returns source citations with page-level references
- Explicitly communicates confidence and policy decisions
- Exposes a versioned, schema-driven API with traceable requests

This is not a chat interface. It is an internal service meant to be consumed by other systems or tools.

## What this system does not do

- It does not claim to be multi-tenant or internet-facing
- It does not include authentication or access control (out of scope for v1)
- It does not attempt to answer questions without supporting documents
- It does not hide uncertainty or fabricate answers

These constraints are deliberate and reflect real internal tooling tradeoffs.

## Design goals

- Reliability over cleverness  
- Explicit failure modes  
- Auditable outputs with citations  
- Clear separation between ingestion, retrieval, policy, and generation  
- Reproducible local development  

## Current status

- API contracts and schemas are complete
- Multi-collection support is implemented at the contract level
- Endpoints are running in contract-only mode
- Retrieval, PDF parsing, and evaluation will be added incrementally

## Quick start

```bash
make venv
make install
make run
