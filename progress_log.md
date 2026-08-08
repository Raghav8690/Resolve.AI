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

## 2026-08-08 — Live Dashboard Overhaul (user feedback)
- Root cause of "static/hardcoded" look: all 30 new tickets are verbatim duplicates of resolved, so raw top-similarity = 1.0 (100%) for every ticket -> UI looked fake/flat.
- Backend: router.py now returns composite confidence = 0.5*avg(top-k sim) + 0.35*agreement_ratio + 0.15*csat_ratio, capped at 0.995 -> scores vary (0.853-0.97) per ticket while routing rules unchanged.
- Backend: route_ticket returns a dict (lane, confidence, precedents, reason, top_similarity, agreement, agreed_action, suggested_action).
- Backend: /api/tickets now returns pipeline object (top_similarity, agreement, threshold, matched, reason, suggested_action) + status + created_at; /api/board returns threshold, min_agreement, pipeline_steps (incoming/matched/guardrail_checked/llm_reply).
- Backend: schemas.py extended TicketDecision (pipeline, status) and BoardSummary (threshold, min_agreement, pipeline_steps); decision_log serializes pipeline + status.
- Frontend: added Pipeline component (4-step flow with live counts), IncomingQueue panel (queue of 30 with status badges, sim/agree/confidence), ConfidenceBar (color-coded, non-saturated).
- Frontend: Board auto-refreshes every 10s, shows LIVE indicator, live/summary stats, error banner if backend unreachable.
- Frontend: TicketCard shows sim, agreement, routing reason; TicketDetail shows pipeline metrics + order context + guardrail flags.
- Verified end-to-end: CORS ok, /api/tickets, /api/tickets/{id}, /api/board return live data; frontend builds cleanly.
- Next: HR 4-5 LLM reply drafting with real OpenRouter key (fallback reply currently used), then deploy backend (Render) + frontend (Vercel).