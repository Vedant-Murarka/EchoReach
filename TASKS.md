# EchoReach — 24-Hour Task Breakdown

Legend: 🅰 Member A / 1 (Orchestration/Agents) · 🅱 Member B / 2 (Backend/Integrations) · 🅲 Member C / 3 (Frontend/Demo)

---

## Hour 0–2 — Setup & Contracts

- [x] 🅰🅱🅲 Finalize agent node list, API contract (request/response shapes for `/leads`, `/leads/{id}`, `/leads/{id}/approve`, `/leads/{id}/decision-log`, `/replies/{id}/correct`)
- [x] 🅰 Set up LangGraph project skeleton, define `LeadState` schema (`app/agents/state.py` with lead info, touch_number, status, research_facts, draft, genericness feedback, classification, decision trace)
- [x] 🅱 Set up FastAPI project, SQLite + Supabase/PostgreSQL SQLAlchemy models: `leads`, `touches`, `decision_log`, `suppression_list`, `simulated_inbox`, `replies`, `classifier_feedback`
- [x] 🅱 Enhance database engine with PostgreSQL/Supabase connection string normalization and connection pool settings (`app/database.py`)
- [x] 🅰 Set up unified LLM Client supporting Google Gemini (`google-genai`), Groq (`groq`), OpenAI, and resilient offline heuristic fallback (`app/agents/llm_client.py`)
- [x] 🅱 Get Tavily/Serper search integration ready with plantable synthetic intelligence fallback (`app/services/search_service.py`)

## Hour 2–8 — Core Pipeline v1

- [x] 🅰 Build Research Agent node: takes lead → calls web_search → extracts structured research facts + sources with kept reasons (`app/agents/research_agent.py`)
- [x] 🅰 Build Drafting Agent node: takes research facts + touch number + channel → returns personalized subject/body referencing $\ge 2$ facts inline (`app/agents/drafting_agent.py`)
- [x] 🅱 Wire Research + Drafting nodes into FastAPI endpoints, persist output to `leads`/`touches` tables (`app/routers/leads.py`)
- [x] 🅱 Build synthetic lead + company dataset (15 leads with plantable facts and suppression records in `seed_data.py`)
- [x] 🅰🅱 Checkpoint: run Research → Draft for one real lead end-to-end and verify output quality in Pytest

## Hour 8–14 — Sequencing, Approval Queue, Reply Loop

- [x] 🅰 Build Genericness Checker node (evaluates draft specificity, detects banned generic phrases, rejects weak drafts, retries with feedback, max 2 retries in `app/agents/genericness_checker.py`)
- [x] 🅰 Build Sequence Planner node (cadence state machine: Day 0 / Day 3 / Day 7 / Day 12, multi-channel rotation in `app/agents/sequence_planner.py`)
- [x] 🅱 Build Human Approval Queue endpoints (`/leads/{id}/approve` with approve/edit/reject) + guardrails: daily send cap counter, suppression list check (`app/services/guardrails.py`)
- [x] 🅱 Build "sandbox send" — writes delivered messages to `simulated_inbox` table to ensure 0 external sends
- [x] 🅱 Build Prospect Persona Simulator (`/leads/{id}/simulate-reply` with 5 personas: Eager Buyer, Skeptic, Out-of-Office, Hard No, Ghost in `app/services/simulator.py`)
- [x] 🅰 Build Reply Classifier node (5-class intent classifier + confidence scoring + reasoning in `app/agents/reply_classifier.py`)
- [x] 🅰 Build Next-Step Decision Agent node (hybrid rule+LLM engine: Escalate to Slack/Discord webhook / Objection Handling Draft / Pause OOO / Stop Opt-out / Advance Sequence in `app/agents/next_step_agent.py`)
- [x] 🅱 Set up Discord/Slack webhook dispatcher for high-intent escalation events (`app/services/webhook.py`)

## Hour 14–18 — Integration Pass 1 + Reasoning Trace (Priority Wow Feature)

- [x] 🅰 Wire full LangGraph state machine together: Research → Draft → Genericness Check (retry loop) → Human Approval Queue → Sequence Planner → Sandbox Send → Reply Classifier → Next-Step Agent (`app/agents/graph.py`)
- [x] 🅱 Ensure every agent node writes structured entries to `decision_log` table (agent name, input summary, reasoning, output summary, timestamp) for the real-time reasoning trace UI
- [x] 🅰🅱 End-to-End Test Suite: 13 automated tests covering all 6 nodes, state transitions, API endpoints, and graph execution (`tests/test_agents_langgraph.py`, `tests/test_backend.py`)
- [x] 🅰🅱 End-to-End Terminal Demo Script running all 6 steps seamlessly (`demo_run.py`)

## Hour 18–20 — Polish & Wow Features

- [x] 🅰 **Self-Improving Classifier Engine (Wow Feature #4)**: Store human corrections in `classifier_feedback` table (`POST /replies/{id}/correct`), dynamically inject into prompt as few-shot exemplars on subsequent classification calls
- [x] 🅰🅱 **Supabase PostgreSQL & Cloud Deployment Ready**:
  - `Dockerfile` (Production container)
  - `render.yaml` (1-click free deployment on Render)
  - `fly.toml` (1-click deployment on Fly.io)
  - `supabase_schema.sql` (Database migration script)
- [x] 🅱 Analytics API (`GET /analytics`) computing pipeline funnel and reply rate distribution by class
- [x] 🅱 Global and per-lead Decision Log APIs (`GET /decision-log`, `GET /leads/{id}/decision-log`)

## Definition of "done" for judging (self-check before demo)

- [x] Every one of the 5 D2 key features is visibly implemented and demonstrated
- [x] The compulsory human-approval-with-guardrails add-on is verified (Daily send cap + suppression list)
- [x] Live agent-to-agent hand-off is visible in the graph (Genericness Checker retry loop)
- [x] The decision log / reasoning trace is persisted for every agent action
- [x] No real external contact is ever messaged — 100% sandboxed sends in `simulated_inbox`
- [x] Self-improving classifier few-shot memory feedback loop implemented and tested
