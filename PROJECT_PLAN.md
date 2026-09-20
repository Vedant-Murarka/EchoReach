# EchoReach — Personalized Multi-Touch Sales Outreach Agent
### Capabl Agentic AI Saksham — Track D2 | 3-member team | 24-hour build

---

## 1. One-line pitch

EchoReach is a stateful multi-agent system that researches a lead, drafts a personalized multi-touch outreach sequence (email + LinkedIn-style DM), waits for human sign-off, watches for replies, classifies intent, and autonomously decides whether to continue, escalate, or stop — with every decision logged and explainable.

This directly targets the four compulsory pieces of D2: per-lead research, personalized drafting, multi-touch sequencing, reply classification + adaptive next-step, plus the compulsory add-on (human approval queue with send guardrails).

---

## 2. Why this design wins on the evaluation rubric

| Rubric criterion | How EchoReach addresses it |
|---|---|
| Personalization quality | Every draft node is forced to cite ≥2 concrete research facts inline; a "genericness checker" agent rejects drafts that don't reference research |
| Sequence logic soundness | Explicit cadence state machine (Day 0 → Day 3 → Day 7 → Day 12), touch intent escalates (intro → value → social proof → breakup) |
| Reply classification accuracy | 5-class LLM classifier with confidence score + human override, few-shot examples stored and reused |
| Escalation appropriateness | Rule + LLM hybrid: hard rules (e.g. "Interested" → always escalate) layered with LLM judgment on ambiguous replies |
| Agentic-ness (implicit but central) | LangGraph state machine with 5 distinct agent nodes, visible hand-offs, a live "reasoning trace" panel judges can literally watch |

---

## 3. Team (3 people) — role split

Roles are split by **pipeline ownership**, not by frontend/backend, so every person can demo their own agent end-to-end.

### Member A — Orchestration & Agent Logic Lead
Owns the LangGraph state machine: Research Agent, Drafting Agent, Genericness-Checker, Sequence Planner, Reply Classifier, Next-Step Decision Agent. Owns prompt engineering and the decision-log schema.

### Member B — Backend, State & Integrations Lead
Owns FastAPI service, Postgres/SQLite schema, per-lead state persistence, web-search tool integration (Tavily/Serper), sandboxed email (Gmail API test mode or simulated inbox), the "prospect persona" reply-simulator (for live demo), and Slack/Discord webhook escalation.

### Member C — Frontend & Demo Lead
Owns the Next.js dashboard: lead pipeline board, human approval queue, per-lead timeline with reasoning trace, analytics view, and the live demo script/data. Also owns synthetic lead + company dataset creation.

All three pair up for the final 2 hours (integration + demo rehearsal).

---

## 4. System architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Next.js Dashboard                          │
│  Pipeline Board │ Approval Queue │ Lead Timeline │ Analytics       │
└───────────────────────────┬───────────────────────────────────────┘
                             │ REST (FastAPI)
┌───────────────────────────▼───────────────────────────────────────┐
│                     FastAPI Orchestration Layer                    │
│                                                                     │
│   ┌──────────────┐   ┌──────────────┐   ┌─────────────────────┐   │
│   │  Research    │──▶│  Drafting    │──▶│ Genericness Checker │   │
│   │  Agent       │   │  Agent       │   │ (reject & retry)    │   │
│   └──────────────┘   └──────────────┘   └──────────┬──────────┘   │
│         ▲                                            │              │
│   web_search tool                                     ▼              │
│   (Tavily/Serper)                          ┌─────────────────────┐  │
│                                             │ Human Approval Queue│  │
│                                             │  (send guardrails)  │  │
│                                             └──────────┬──────────┘  │
│                                                         ▼             │
│   ┌──────────────┐   ┌──────────────┐   ┌─────────────────────┐    │
│   │ Reply         │◀──│ Simulated /   │◀──│  Sequence Planner   │    │
│   │ Classifier    │   │ Sandbox Send  │   │  (cadence engine)   │    │
│   └──────┬───────┘   └──────────────┘   └─────────────────────┘    │
│          ▼                                                            │
│   ┌──────────────────┐                                               │
│   │ Next-Step Decision│──▶ continue / pause / escalate (Slack) / stop │
│   │ Agent             │                                               │
│   └──────────────────┘                                               │
│                                                                        │
│   Every node writes to: decision_log table (agent, input, reasoning, │
│   output, timestamp) — this powers the reasoning-trace UI            │
└────────────────────────────────────────────────────────────────────┘
                             │
                   ┌─────────▼─────────┐
                   │ Postgres / SQLite │
                   │ leads, touches,   │
                   │ decision_log      │
                   └───────────────────┘
```

LangGraph is the natural fit here because the pipeline is genuinely **stateful per lead** (a lead can sit at any node depending on where it is in its sequence) rather than a single linear chain — this is what separates it from "three features glued together" in the judges' eyes.

---

## 5. Agent-by-agent detail

### 5.1 Research Agent
- Input: lead name, title, company, LinkedIn URL (mock)
- Tool calls: `web_search(company_name + "news")`, `web_search(person_name + role)`
- Output: 3–5 bullet "research facts" with source, tagged by type (news / role-change / funding / hiring / product-launch)
- Logs its tool calls and why each fact was kept

### 5.2 Drafting Agent
- Input: research facts + current touch number + channel (email/LinkedIn)
- Touch-intent map:
  - Touch 1 (Day 0): Intro — reference 1 research fact, soft CTA
  - Touch 2 (Day 3): Value — tie research fact to a specific pain point
  - Touch 3 (Day 7): Social proof — case study relevant to their industry
  - Touch 4 (Day 12): Breakup — polite close, leaves door open
- Output: subject + body, with research facts used marked/highlighted

### 5.3 Genericness Checker (wow feature #1)
- Scores the draft: does it reference ≥2 specific facts? Any generic filler phrases from a banned-phrase list?
- If it fails, sends the draft back to the Drafting Agent with feedback (max 2 retries) — this is a visible agent-to-agent hand-off judges can see in the trace

### 5.4 Human Approval Queue (compulsory add-on)
- Every draft lands here before "sending" — nothing auto-sends
- Guardrails: daily send cap per rep, suppression list (do-not-contact), duplicate-contact check
- Approve / Edit / Reject actions, all logged

### 5.5 Sequence Planner
- State machine per lead: tracks which touch number is next, cadence timing, channel rotation
- Decides whether it's time to fire the next touch or wait

### 5.6 Reply Classifier
- 5 classes: Interested / Not Interested / Objection / Out-of-Office / No Reply (timeout)
- LLM few-shot classifier + confidence score
- Human can correct a misclassification; correction is stored and fed back as a few-shot example (self-improving loop, same pattern as the PDF's other compulsory add-ons)

### 5.7 Next-Step Decision Agent
- Interested → escalate to human rep immediately (Slack/Discord webhook)
- Objection → draft an objection-handling reply, back to approval queue
- OOO → auto-pause sequence for N days, resume automatically
- Not Interested → stop sequence, log reason
- No reply after timeout → advance to next touch

---

## 6. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | LangGraph | Native stateful per-lead graph, visible node hand-offs |
| Backend | FastAPI (Python) | Fast to build, async, matches team's existing stack |
| LLM | Claude (Anthropic API) or Groq/Llama for speed | Claude for drafting quality; Groq as fast fallback for classification calls |
| Web search | Tavily API (free tier, agent-friendly) or Serper | Purpose-built for agentic search, clean JSON output |
| Database | SQLite for the hackathon (zero-setup) → schema portable to Postgres | Speed of setup matters more than scale on demo day |
| ORM | SQLAlchemy | Team familiarity, quick schema iteration |
| Frontend | Next.js + Tailwind + shadcn/ui | Team's existing stack, fast to build a clean dashboard |
| Charts | Recharts | Analytics view (funnel, reply-rate) |
| Messaging (sandboxed) | Simulated inbox table + optional Gmail API test-mode send to team's own addresses | Never sends to real external contacts, per the PDF's explicit note |
| Escalation | Discord/Slack Incoming Webhook | One-line integration, high demo impact |
| Deployment | Docker Compose (backend+db) + Vercel for frontend, or all-local for demo | Keep it simple; a working local demo beats a half-working deployed one |

---

## 7. Compulsory feature checklist (from the PDF)

- [x] Per-lead research agent pulling public context
- [x] Personalized drafting referencing specific research points
- [x] Multi-touch sequence planner with defined cadence + escalating intent
- [x] Reply-classification agent (5 classes)
- [x] Adaptive next-step agent (continue / pause / escalate / stop)
- [x] Stateful per-lead pipeline with persistent state
- [x] Visible decision log
- [x] **Compulsory add-on: human approval queue with send guardrails** (suppression list + daily cap)
- [x] Sandbox-only sending, synthetic/team-member leads only

## 8. Wow features (beyond the brief, ranked by effort:impact)

1. **Live reasoning-trace panel** — a real-time feed showing each agent's input → reasoning → output, styled like a chat log between agents. This single feature does more for the "agentic, not chatbot" scoring lens than anything else — build this even under time pressure.
2. **Prospect Persona Simulator** — an LLM "plays" the prospect and generates a realistic reply in real time during the demo, so judges see the *full loop* (draft → approve → simulated send → reply → classify → decide) live, without needing a real inbox.
3. **Genericness Checker retry loop** — visibly rejects a lazy draft and forces a rewrite, live, in front of judges.
4. **Self-improving classifier** — human corrections to classification are stored and immediately used as few-shot examples for the next call (same pattern as the PDF's C3 feedback-loop add-on, applied here).
5. **Analytics dashboard** — reply-rate by touch number, funnel drop-off, "which research-fact type performs best" chart (nice stretch if time allows in hour 20–22).
6. **Suppression + daily-cap guardrail UI** — visually shows the cap ticking down, reinforces the safety story.

Priority order if time runs short: build 1–3 first; 4–6 are true stretch goals, drop them without guilt if hour 20 arrives and core pipeline isn't rock solid.

---

## 9. Data plan

- 15–20 synthetic leads (name, title, company, fake LinkedIn/company blurb) generated by an LLM up front, tagged with 2–3 "plantable" research facts each so demo research calls return clean, relevant hits
- 4–5 pre-scripted "prospect personas" for the reply simulator (an eager buyer, a skeptic with objections, a ghost, an OOO auto-reply, a hard no) so the classifier gets exercised across all 5 classes during the live demo

## 10. Demo script (aim for 4–5 minutes)

1. Show pipeline board — 5 leads at different sequence stages (10s)
2. Open one lead → show Research Agent's pulled facts with sources (20s)
3. Show the Genericness Checker rejecting a weak draft and forcing a retry — live reasoning trace visible (30s)
4. Approve the good draft from the Human Approval Queue, point out the daily-cap/suppression guardrail (20s)
5. Trigger the Prospect Persona Simulator to "reply" as an interested prospect (30s)
6. Show Reply Classifier tag it Interested + Next-Step Agent escalate to Slack in real time (30s)
7. Switch to a second lead, trigger an Objection-class reply, show the agent draft an objection-handling follow-up instead of escalating (30s)
8. Close on the analytics dashboard + decision log for full explainability (20s)

---

## 11. Risk register

| Risk | Mitigation |
|---|---|
| Real web search returns noisy/irrelevant results live | Cache/pin known-good results for demo leads; live search as a bonus, not a dependency |
| LLM rate limits during demo | Use a faster/cheaper model (Groq/Llama) for classification, reserve Claude/GPT for drafting only |
| LangGraph state bugs under time pressure | Keep the graph to 6 nodes max; test the full loop end-to-end by hour 14, not hour 23 |
| Frontend polish eating backend time | Member C builds UI against a mocked API first (hour 2), swaps to real API once ready — never blocks on backend |
