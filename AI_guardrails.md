# AI Agent Guardrails — Zepto Support Ticket Manager

Purpose: keep the coding agent inside PS-context.md + features.md scope. Every deviation below costs
build time and tokens that don't move the rubric. If a task isn't in features.md, don't do it.

## 1. Scope Lock
- Do NOT build anything from the Bonus row (approve/override controls, live ticket-stream simulation,
  embeddings) unless every checklist item in features.md sections 1-11 is checked off and confirmed working.
- Do NOT add features not listed in features.md — no auth/login, no user roles, no admin panel, no
  settings page, no notifications, no analytics dashboard, no export-to-CSV, no dark mode.
- Do NOT expand the frontend beyond the two-lane board + ticket detail view. One page, as specified.
- Do NOT add extra API endpoints beyond the 3 listed in features.md §8. If a new endpoint seems useful,
  ask first — don't build it speculatively.

## 2. Algorithm Discipline
- TF-IDF + cosine similarity is final for this build. Do NOT swap in embeddings, BM25, or any other
  similarity method mid-build, even if "better" — that's the bonus-row swap, later only.
- Do NOT tune the confidence threshold repeatedly without a reason. Set it once from PS-context.md
  guidance, test against the 4 demo scenarios, adjust only if a scenario fails — not out of curiosity.
- Do NOT re-vectorize or re-fit TF-IDF on every request. Fit once on `resolved_tickets.csv`, cache/reuse
  the vectorizer and matrix.

## 3. LLM Call Discipline (this is where tokens actually get burned)
- Only two things get an LLM call: (1) reply drafting, (2) explanation text if you choose to generate it
  rather than template it. Routing, guardrail checks, and action selection are plain Python logic —
  NEVER route these through an LLM call.
- Do NOT call the LLM per precedent ticket. One call per new ticket, with the top-3 precedents passed in
  as context — not three separate calls.
- Do NOT pass the full `resolved_tickets.csv` into any prompt. Pass only the retrieved top-3 rows.
- Do NOT re-generate a reply or explanation on every page load/re-render. Generate once when the ticket
  is processed, store the result, serve it from storage after that.
- Keep prompts short and directive — no multi-paragraph system prompts, no few-shot examples unless a
  reply is coming out clearly wrong. Start minimal, add only if quality demands it.
- Do NOT use the LLM to "double-check" or "validate" what deterministic code already decided (e.g. don't
  ask the LLM to re-verify the refund cap — that's a code guardrail, not an AI judgment call).

## 4. Code Discipline
- Do NOT refactor or rewrite working code "for cleanliness" mid-build. If it passes its test in
  features.md, leave it — refactor only in the final buffer hour if time allows.
- Do NOT add new dependencies beyond: pandas, scikit-learn, FastAPI (or Flask), a frontend framework of
  choice, and the LLM SDK. No ORMs, no task queues, no caching layers, no Docker unless deployment
  requires it.
- Do NOT invent new data fields not present in the 3 CSVs. If a field seems missing, flag it — don't
  synthesize fake data to fill the gap.
- Do NOT write speculative error handling for inputs that don't exist in the dataset (e.g. malformed
  CSVs, missing files). Handle the data as given.

## 5. Documentation & Output Discipline
- Do NOT generate long docstrings, inline comments explaining obvious code, or verbose README sections
  beyond: setup steps, threshold logic explanation, and how to run it.
- Do NOT produce extra summary files, progress reports, or explanatory markdown beyond what's asked for.
- When asked to build a feature, output the code — not a lengthy explanation of the approach first,
  unless explicitly asked to explain.
- Do NOT re-explain PS-context.md or features.md back before doing the work. Reference them, don't repeat them.

## 6. Testing Discipline
- Test only against the cases already defined in features.md. Do NOT write additional edge-case tests
  for scenarios outside the dataset or outside the 4 demo scenarios.
- Do NOT build a full automated test suite/CI pipeline — manual verification against the checklist is
  sufficient for a 10-12h hackathon build.

## 7. When In Doubt
- If a task isn't explicitly in features.md or PS-context.md, ask before building it rather than
  assuming it's wanted.
- Default to the smallest implementation that passes the listed test — not the most robust,
  extensible, or "production-grade" one. This is a 10-12h build, not a product.
