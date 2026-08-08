# PS Context — Zepto Support Ticket Manager
DigiPlus IT Agentic AI Hackathon · 10-12hr offline build · TCET

# Goal
"Build the most complete, reliable and explainable support-resolution product that can be demonstrated live."

## 1. The Real-World Problem

Zepto (10-minute delivery) receives thousands of support tickets daily: "items missing," "order late,"
"wrong item," "refund not received." The core insight driving this PS: **~90% of these tickets are not new
problems** — they are near-duplicates of tickets already resolved hundreds of times before. Yet today, every
single ticket — routine or not — waits in the same queue for a human agent to read it from scratch and make
a decision that history already knows.

This creates two compounding costs:
- **Latency cost**: a routine "milk packet missing" ticket sits for hours behind a backlog, when the correct
  action (refund ₹40) was already decided the last 4,000 times an identical ticket appeared.
- **Attention cost**: unusual, genuinely novel tickets (the ones that actually need human judgment) get no
  priority — they wait in the exact same line as trivial repeats, so the hardest problems get the least
  attention relative to their difficulty.

## 2. What "Solving This" Actually Means

The PS is not asking you to build a generic ticket classifier. It's asking you to build a **precedent-based
decision system** — the same logic a very experienced human agent uses ("I've seen this exact ticket before,
I know what to do") but automated and made explainable. Three things must be true of the solution:

1. **Every decision must be traceable to precedent.** No ticket gets auto-resolved because a model "felt"
   confident — it gets resolved because 3 near-identical past tickets were resolved the same way.
2. **The system must know what it doesn't know.** A novel ticket with weak precedent matches must NOT be
   guessed at — it goes to a human, full stop. This is the most heavily validated behavior in the PS (see
   validation scenarios below) — get this wrong and the "working solution" score (30% of the rubric) takes
   the biggest hit.
3. **Actions must respect real-world constraints**, not just pattern-match text. A refund can't exceed the
   order value. A cancelled order can't get a redelivery. The order context data exists specifically to
   catch these — ignoring it means the system can produce actions that are text-plausible but factually wrong.

## 3. Data — What Each File Is For

| File | Role | Key columns to reason about |
|---|---|---|
| `resolved_tickets.csv` | The "memory" — precedent database | description (text to match against), action taken, resolution note, CSAT (signals whether the past action was actually a *good* outcome, not just *an* outcome) |
| `new_tickets.csv` | The incoming queue to process | description, linked order ID |
| `orders_context.csv` | Ground truth that constrains what actions are even valid | items, order value, delivery time, status (this is your guardrail data — cancelled/delivered/in-transit status changes what actions make sense) |

**Important nuance**: `resolved_tickets.csv`'s CSAT column is easy to ignore but matters — if you have time,
weighting precedent matches by CSAT (prefer precedents that made customers happy, not just any past action)
is a cheap way to add technical depth without adding much build time.

## 4. The Decision Pipeline (What You're Actually Building)

```
new ticket text
      │
      ▼
TF-IDF vectorize + cosine similarity vs. resolved_tickets
      │
      ▼
Top-3 most similar past tickets retrieved
      │
      ▼
Do the top-3 AGREE on the action taken?
      │
   ┌──┴──┐
  YES    NO / weak similarity
   │       │
   ▼       ▼
Check order_context guardrails      Route to human lane
(refund ≤ order value,              (attach the top-3 precedents +
 status allows this action)          a suggested action anyway,
   │                                 so the human isn't starting cold)
   ▼
Apply action + draft reply
(cite the precedents as "why")
```

The **confidence threshold** is the single most important design decision in this PS. It has two knobs:
- **Similarity score** of the top match (how textually close is this to something we've seen?)
- **Agreement** among the top-3 (do they even suggest the same action?)

A defensible default: auto-resolve only if top similarity ≥ ~0.6 **and** at least 2 of the top-3 agree on
the action. Anything else goes to the human lane. Document this threshold explicitly — evaluators will ask
"why this number," and "we tested it against a few sample tickets and this is where false-auto-resolves
stopped happening" is a perfectly good answer.

## 5. Validation Scenarios — Read These as Your Test Cases, Not Just Requirements

- A clear missing-item ticket with strong precedents → auto-resolved, same action as history, refund never
  exceeds order value, reply cites its top-3 precedents by name/reference.
- A genuinely novel ticket with low similarity → human lane, never guessed at.
- Top-3 precedents disagree on action → queued for human, not resolved on a majority-of-one guess.
- A ticket tied to a cancelled order → never triggers redelivery, regardless of what the text similarity says.

Treat each of these as a literal test you should manually run before the demo. If you can walk the panel
through these four scenarios live, you are directly answering the rubric's "working solution" (30%) and
"technical depth" (25%) criteria in one shot.

## 6. Where the AI Layer Actually Earns Points

Two distinct jobs, don't conflate them:
1. **Decision explanation** — "why this action?" answered by naming the precedent tickets and what they had
   in common. This can be templated (no LLM call strictly required) or LLM-generated from the retrieved
   precedents — either is fine, but it must be grounded in the actual retrieved rows, not invented.
2. **Reply drafting** — a customer-facing message. This is where an LLM call adds real value: personalize
   tone, reference the specific order, state the resolution clearly. Keep the prompt scoped to just this
   ticket + its action + order facts — don't let the model freelance beyond what was decided upstream.

## 7. Scope Discipline

Build order that keeps you demo-safe at every hour mark:
1. TF-IDF similarity + top-3 retrieval working on real data (prove this first — it's the foundation everything else depends on)
2. Confidence threshold + auto vs. human routing logic
3. Order-context guardrails (refund cap, cancelled-order block)
4. Backend API wrapping the above
5. Reply drafting + why-explanation (LLM layer)
6. Two-lane frontend board
7. Deploy + public repo

Bonus-row items (approve/override controls, live ticket-stream simulation, embeddings instead of TF-IDF) are
explicitly last — only touch them once steps 1-7 are fully working and deployed.
