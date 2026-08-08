# Resolve.AI — Progress Log

## 2026-08-08 — Project Initialization
- Analyzed PS-context.md, features.md, AI_guardrails.md
- Confirmed: CSV files ready in sample_data/, OpenRouter (Nemotron-3-Ultra) for LLM, React+Vite frontend
- Planned folder structure and 8-hour build schedule
- Copied CSVs to data/ directory
- Next: Hour 1 - Data loader + TF-IDF similarity core

## 2026-08-08 — Hour 1: Data Layer + TF-IDF Core
- Created folder structure (backend/, frontend/, data/)
- Implemented data_loader.py: load CSVs, join new_tickets -> orders_context, clean text
- Implemented similarity.py: TF-IDF fit on resolved_tickets, transform new tickets, cosine similarity, top-3 retrieval (fit once, cached)
- Implemented config.py with thresholds (SIMILARITY_THRESHOLD=0.6, MIN_AGREEMENT=2, TOP_K=3)
- Implemented schemas.py with Pydantic models
- Verified top-3 retrieval: "milk packet missing" -> H-1000/H-1173/H-1152 (sim 1.0); unrelated text -> sim 0.0
- Python 3.14 required unpinned deps: fastapi, uvicorn, pandas, scikit-learn, openai, python-dotenv, pydantic
- Installed deps successfully: pandas 3.0.5, scikit-learn 1.9.0, openai 2.53.0, numpy 2.5.1

## 2026-08-08 — Hour 2: Routing + Guardrails
- Implemented router.py: confidence threshold + top-3 agreement logic
- Implemented guardrails.py: refund cap, cancelled-order redelivery block
- Implemented explanation.py: templated "why" text citing precedent IDs
- Implemented llm_reply.py: single OpenRouter call per ticket with order facts + action (fallback reply if no API key)
- Implemented actions.py: simulate refund/redelivery/coupon actions (logging moved to decision_log.py to avoid schema collision)
- Implemented decision_log.py: JSONL append-only log + board summary
- Built FastAPI endpoints: GET /health, /api/tickets, /api/tickets/{id}, /api/board, POST /api/process
- Validation results: 30 tickets -> 23 auto, 7 human. Guardrail Scenario D confirmed (N-000 cancelled order -> escalation, never redelivery)
- Fixes: actions.py no longer double-writes log; explanation now shows guardrail-block reason correctly

## 2026-08-08 — Frontend (React + Vite)
- Created vite config, package.json, index.html, .env, main.jsx, App.jsx, api.js, styles.css
- Components: Board (two-lane), TicketCard, TicketDetail (precedents + reply + flags), Loading