#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "Health:"
curl -s "$BASE_URL/v1/health" && echo
echo

echo "Ingest sample PDFs:"
curl -s -X POST "$BASE_URL/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "handbook",
    "source": { "type": "local_folder", "path": "data/pdfs/handbook" },
    "rebuild_index": true
  }' && echo
echo

echo "Ask:"
curl -s -X POST "$BASE_URL/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"collection_id":"handbook","question":"What is the PTO policy?","top_k":5,"max_context_chunks":6}' \
  | python -c "import sys,json; r=json.load(sys.stdin); print(r['policy_action'], r['confidence']); print('citations:', len(r['citations']))"
echo

echo "Stats:"
curl -s "$BASE_URL/v1/collections/handbook/stats" && echo

echo
echo "E2E smoke test complete."
