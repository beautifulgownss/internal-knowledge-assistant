.PHONY: venv install run health ask

venv:
	python3 -m venv .venv

install:
	. .venv/bin/activate && pip install --upgrade pip && pip install fastapi uvicorn pydantic

run:
	. .venv/bin/activate && uvicorn app.main:app --reload

health:
	curl -s http://127.0.0.1:8000/v1/health && echo

ask:
	curl -s -X POST "http://127.0.0.1:8000/v1/ask" \
	  -H "Content-Type: application/json" \
	  -d '{"collection_id":"handbook","question":"What is the PTO policy?","top_k":5,"max_context_chunks":6}' && echo
