# Feature Checklist — Zepto Support Ticket Manager

## 1. Data Layer
- [ ] Load `resolved_tickets.csv`, `new_tickets.csv`, `orders_context.csv` into pandas
- [ ] Join `new_tickets` → `orders_context` on order ID
  - **Test:** every new ticket resolves to exactly one order row; no nulls after join
- [ ] Clean/normalize ticket description text (lowercase, strip punctuation) for both resolved and new tickets
  - **Test:** spot-check 5 descriptions before/after — no words mangled, no empty strings produced

## 2. Similarity Matching (TF-IDF)
- [ ] Fit TF-IDF vectorizer on `resolved_tickets.description`
- [ ] Transform new ticket descriptions into the same vector space
- [ ] Compute cosine similarity of each new ticket against all resolved tickets
- [ ] Return top-3 most similar resolved tickets per new ticket
  - **Test:** a ticket that's a near-duplicate of a known resolved ticket (e.g. same "milk packet missing" phrasing) returns that ticket as #1 match with high similarity (>0.7)
  - **Test:** a ticket with unrelated wording (e.g. "app keeps crashing") returns low similarity scores (<0.3) across the board

## 3. Confidence & Routing Logic
- [ ] Define similarity threshold (e.g. top match ≥ 0.6)
- [ ] Define agreement rule (e.g. ≥2 of top-3 precedents agree on action)
- [ ] Route: both conditions met → auto-resolve lane; either fails → human lane
  - **Test:** clear missing-item ticket with strong, agreeing precedents → routes to auto-resolve
  - **Test:** novel ticket with weak similarity → routes to human lane, never auto-resolved
  - **Test:** ticket where top-3 precedents disagree on action (e.g. one refunded, one redelivered, one gave coupon) → routes to human lane even if similarity is high

## 4. Order-Context Guardrails
- [ ] Refund amount capped at order value (never exceeds it)
- [ ] Redelivery action blocked if order status = cancelled
- [ ] Redelivery/refund blocked or flagged if order status is inconsistent with the complaint (e.g. "item missing" on an order still in transit)
  - **Test:** ticket linked to a cancelled order never produces a redelivery action, regardless of text similarity to redelivery precedents
  - **Test:** proposed refund amount is checked against and never exceeds that ticket's order value

## 5. Action Execution (Simulated)
- [ ] Simulate refund action (amount, ticket ID, timestamp logged)
- [ ] Simulate redelivery action (order ID, timestamp logged)
- [ ] Simulate coupon action (code, value, ticket ID logged)
- [ ] Log every decision: ticket ID, lane (auto/human), action, confidence score, precedents used
  - **Test:** every auto-resolved ticket has a corresponding log entry with all fields populated
  - **Test:** no action is applied to a human-lane ticket (actions are only simulated post-decision, not pre-emptively)

## 6. AI Layer — Explanation
- [ ] Generate "why this action" text citing the specific top-3 precedent tickets used
  - **Test:** explanation text references real precedent ticket content — no unexplained/invented reasoning
  - **Test:** for a human-lane ticket, explanation states *why* it wasn't auto-resolved (low similarity / disagreement)

## 7. AI Layer — Reply Drafting
- [ ] Generate customer-facing reply referencing order facts + resolution action
- [ ] Reply tone appropriate to action (apology + refund confirmation vs. apology + redelivery ETA, etc.)
  - **Test:** reply mentions correct order details (not hallucinated items/values)
  - **Test:** reply text matches the action actually taken (no reply promising redelivery when action was refund)

## 8. Backend API
- [ ] Endpoint: submit/list new tickets with routing decision
- [ ] Endpoint: get ticket detail (precedents, confidence, action, reply)
- [ ] Endpoint: board summary (counts auto-resolved vs human lane)
  - **Test:** each endpoint returns valid JSON for a sample ticket ID
  - **Test:** board summary counts match the actual number of logged decisions

## 9. Frontend — Two-Lane Board
- [ ] Auto-resolved lane: list view with ticket, action, confidence
- [ ] Human-review lane: list view with ticket, suggested action, confidence, precedents attached
- [ ] Ticket detail view: top-3 precedents, confidence score, drafted reply
  - **Test:** clicking a ticket in either lane shows its precedents and reasoning without a page error
  - **Test:** lane counts on the board match the backend summary endpoint

## 10. Deployment
- [ ] Backend deployed to free-tier host (Render/Railway/etc.)
- [ ] Frontend deployed and pointing at live backend URL (not localhost)
- [ ] Public GitHub repo with README explaining setup + threshold logic
  - **Test:** live URL loads and successfully processes a sample new ticket end-to-end (not just static UI)
  - **Test:** repo clones and runs from README instructions alone

## 11. Demo Readiness (Validation Scenarios as Live Tests)
- [ ] Scenario A: clear missing-item ticket → auto-resolved, refund ≤ order value, reply cites top-3 precedents
- [ ] Scenario B: novel ticket → human lane, no guessed action applied
- [ ] Scenario C: disagreeing precedents → human lane despite high similarity
- [ ] Scenario D: cancelled-order ticket → redelivery never triggered
- [ ] Pick these exact 4 tickets ahead of time and rehearse walking through them live

---
**Bonus (only after all above is checked off):**
- [ ] Human approve/override controls with logging
- [ ] Live ticket-stream simulation
- [ ] Swap TF-IDF for sentence-transformer embeddings
