# EchoReach — 24-Hour Task Breakdown

Legend: 🅰 Member A (Orchestration/Agents) · 🅱 Member B (Backend/Integrations) · 🅲 Member C (Frontend/Demo)

---

## Hour 0–2 — Setup & Contracts

- [ ] 🅰🅱🅲 Finalize agent node list, API contract (request/response shapes for `/leads`, `/leads/{id}`, `/leads/{id}/approve`, `/leads/{id}/decision-log`)
- [ ] 🅰 Set up LangGraph project skeleton, define `LeadState` schema (lead info, touch_number, status, research_facts, draft, classification)
- [ ] 🅱 Set up FastAPI project, SQLite + SQLAlchemy models: `leads`, `touches`, `decision_log`, `suppression_list`
- [ ] 🅲 Set up Next.js + Tailwind + shadcn project, build mocked API layer (hardcoded JSON) so frontend work never blocks on backend
- [ ] 🅱 Get Tavily/Serper API key working with a test call
- [ ] 🅰 Get LLM API keys working (Claude + Groq fallback), test a basic call

## Hour 2–8 — Core Pipeline v1

- [ ] 🅰 Build Research Agent node: takes lead → calls web_search → returns tagged research facts + sources
- [ ] 🅰 Build Drafting Agent node: takes research facts + touch number → returns subject/body referencing ≥2 facts
- [ ] 🅱 Wire Research + Drafting nodes into FastAPI endpoint, persist output to `leads`/`touches` tables
- [ ] 🅱 Build synthetic lead + company dataset (15–20 leads with plantable research facts)
- [ ] 🅲 Build Pipeline Board UI (list of leads with stage badges) against mocked API
- [ ] 🅲 Build Lead Detail view skeleton (research facts panel, draft panel, empty timeline)
- [ ] 🅰🅱 Checkpoint: run Research → Draft for one real lead end-to-end, inspect output quality

## Hour 8–14 — Sequencing, Approval Queue, Reply Loop

- [ ] 🅰 Build Genericness Checker node (rejects generic drafts, retries with feedback, max 2 retries)
- [ ] 🅰 Build Sequence Planner node (cadence state machine: Day 0/3/7/12, touch-intent map)
- [ ] 🅱 Build Human Approval Queue endpoints (approve/edit/reject) + guardrails: daily send cap, suppression-list check
- [ ] 🅱 Build "sandbox send" — write to a simulated inbox table instead of a real send
- [ ] 🅱 Build Prospect Persona Simulator endpoint (LLM roleplays a prospect reply given a persona type + the sent draft)
- [ ] 🅰 Build Reply Classifier node (5-class + confidence)
- [ ] 🅰 Build Next-Step Decision Agent node (continue/pause/escalate/stop + rule+LLM hybrid)
- [ ] 🅱 Set up Discord/Slack webhook for escalation events
- [ ] 🅲 Build Human Approval Queue UI (approve/edit/reject buttons, cap counter, suppression check indicator)
- [ ] 🅲 Build reply simulator trigger UI (pick a persona, fire a simulated reply)

## Hour 14–18 — Integration Pass 1 + Reasoning Trace (priority wow feature)

- [ ] 🅰🅱 Wire full LangGraph state machine together: Research → Draft → Genericness Check → Approval → Sequence Planner → (sandbox send) → Reply Classifier → Next-Step Agent
- [ ] 🅱 Ensure every node writes a structured entry to `decision_log` (agent name, input summary, reasoning, output, timestamp)
- [ ] 🅲 Swap frontend from mocked API to real API
- [ ] 🅲 Build the Live Reasoning-Trace panel (poll or WebSocket `decision_log`, render as an agent-to-agent chat feed) — **this is the single highest-priority UI feature, do not skip or cut short**
- [ ] 🅰🅱🅲 Checkpoint: run one lead through the *entire* loop live (draft → approve → simulate reply → classify → escalate) and fix breakage

## Hour 18–20 — Polish + Stretch Features (only if core is solid)

- [ ] 🅰 Self-improving classifier: store human corrections, inject as few-shot examples on next call
- [ ] 🅲 Analytics dashboard (reply-rate by touch, funnel chart) using Recharts
- [ ] 🅲 Visual polish pass on Pipeline Board and Lead Detail view
- [ ] 🅱 Add 2–3 more persona types to the reply simulator for demo variety

## Hour 20–22 — Full Rehearsal & Bug Fixing

- [ ] 🅰🅱🅲 Run the full 8-step demo script twice, timing it
- [ ] 🅰🅱🅲 Fix any bugs surfaced during rehearsal — no new features from this point on
- [ ] 🅲 Prepare backup: screen recording of a clean run, in case live demo hits an API rate limit or network issue

## Hour 22–24 — Buffer, Slides, Final Rehearsal

- [ ] 🅲 Build a short slide deck: problem, architecture diagram, wow features, live demo hand-off
- [ ] 🅰🅱🅲 Final full rehearsal with roles assigned (who talks during which demo step)
- [ ] 🅰🅱🅲 Buffer time for anything that broke — this block is intentionally light, protect it

---

## Definition of "done" for judging (self-check before demo)

- [ ] Every one of the 5 D2 key features is visibly demonstrated, not just implemented
- [ ] The compulsory human-approval-with-guardrails add-on is shown, not just mentioned
- [ ] At least one live agent-to-agent hand-off is visible on screen (Genericness Checker retry is the easiest to show)
- [ ] The decision log / reasoning trace is on screen for at least one full lead lifecycle
- [ ] No real external contact is ever messaged — only sandboxed/simulated sends
