# EchoReach — Personalized Multi-Touch Sales Outreach Agent

[![Track D2](https://img.shields.io/badge/Capabl_Agentic_AI-Track_D2-blue.svg)](https://capabl.ai)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg)](https://python.org)
[![SQLite](https://img.shields.io/badge/Database-SQLite%2FSQLAlchemy-003B57.svg)](https://sqlalchemy.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#license)

**EchoReach** is an autonomous, stateful multi-agent system designed for personalized sales outreach. It researches target leads using live web search, drafts personalized multi-touch sequences (citing inline facts), enforces guardrails (daily send caps + suppression lists), waits for human approval, simulates prospect replies, classifies intent, and autonomously decides adaptive next steps — with every decision logged to a real-time reasoning trace.

Built for **Capabl Agentic AI Saksham — Track D2 (3-Member 24-Hour Hackathon Build)**.

---

## 🎯 1. Team Role Breakdown & Ownership

The project is architected with clear pipeline ownership across 3 team members:

| Member | Role | Key Responsibilities |
|---|---|---|
| **Member 1 (Member A)** | Orchestration & Agent Lead | LangGraph graph topology, prompt engineering, agent node definitions, and graph state contracts. |
| **Member 2 (Member B - Vedant)** | **Backend, State & Integrations Lead** | **FastAPI application, SQLite + SQLAlchemy persistence, web search API integration (Tavily/Serper), Send Guardrails engine, Prospect Persona Simulator, Slack/Discord webhooks, synthetic dataset, decision log API, and testing suite.** |
| **Member 3 (Member C)** | Frontend & Demo Lead | Next.js dashboard, Pipeline Board, Approval Queue UI, Live Reasoning Trace panel, and presentation script. |

---

## 🏗️ 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Next.js Frontend Dashboard                          │
│     Pipeline Board │ Approval Queue │ Lead Timeline │ Reasoning Trace UI   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST API (FastAPI)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Orchestration & Backend Service                  │
│                                                                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌───────────────────────────┐  │
│  │ Research Agent  │──▶│ Drafting Agent  │──▶│ Genericness Checker Agent │  │
│  │ (Search Tool)   │   │ (Touch Intent)  │   │ (Reject & Retry Loop)     │  │
│  └─────────────────┘   └─────────────────┘   └─────────────┬─────────────┘  │
│                                                            │                │
│                                                            ▼                │
│  ┌─────────────────┐   ┌─────────────────┐   ┌───────────────────────────┐  │
│  │ Next-Step Agent │◀──│ Reply           │◀──│ Human Approval Queue      │  │
│  │ (Escalate/Stop) │   │ Classifier      │   │ (Send Guardrails Engine)  │  │
│  └────────┬────────┘   └────────┬────────┘   └─────────────┬─────────────┘  │
│           │                     │                          │                │
│    Slack/Discord            Simulated                 Simulated             │
│       Webhook              Prospect Reply            Sandbox Inbox          │
│                                                                             │
│  Every node logs: decision_log table (agent, input, reasoning, output)      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                             ┌─────────▼─────────┐
                             │  SQLite Database  │
                             │ leads, touches,   │
                             │ decision_log, ... │
                             └───────────────────┘
```

---

## 🚀 3. How to Setup & Run (Step-by-Step)

### Prerequisites
- **Python 3.10+** installed on your system.
- **Git** (optional).

---

### Step 1: Clone or Navigate to Project Directory

```bash
cd c:\Users\Vedant\Documents\PLAN
```

---

### Step 2: Create and Activate Virtual Environment

**On Windows (PowerShell / CMD):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install Required Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4: Configure Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

*(Note: The system works out-of-the-box with built-in heuristic fallbacks even if API keys are left blank!)*

---

### Step 5: Seed Synthetic Lead Dataset

Seed the database with 15 synthetic leads and plantable research facts:

```bash
python seed_data.py
```

*Output:*
```text
Initializing SQLite database tables...
Seeding 15 synthetic leads...
Database seeding completed successfully!
Total Leads Created: 15
Total Research Facts Created: 30
Total Suppression Entries: 2
```

---

### Step 6: Run the Terminal Demo Script

To execute Member 2's end-to-end backend pipeline execution directly in your terminal:

```bash
python demo_run.py
```

This runs the full 6-step loop:
1. Target Lead retrieval (`Apex Dynamics`).
2. Research & Drafting Agent execution with Genericness Checker.
3. Human Approval Queue & Guardrail checks (Daily send cap + suppression check).
4. Sandbox Inbox delivery.
5. Prospect Persona Reply Simulation (`Eager Buyer`).
6. Intent Classification, Next-Step decision, Slack/Discord webhook trigger, and Reasoning Trace output.

---

### Step 7: Launch FastAPI Server

Start the interactive FastAPI backend server:

```bash
uvicorn app.main:app --reload --port 8000
```

or:

```bash
python -m app.main
```

The server will be available at: **`http://127.0.0.1:8000`**

---

### Step 8: Open Interactive API Documentation (OpenAPI / Swagger)

Open your browser and navigate to:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

From here, you can test every REST endpoint interactively.

---

### Step 9: Run Automated Unit & Integration Tests

To run the Pytest test suite:

```bash
pytest -v
```

---

## 📡 4. Key API Endpoints Reference (Member 2 Scope)

| Endpoint | Method | Description |
|---|---|---|
| `GET /leads` | `GET` | List all leads in pipeline (filterable by `stage`). |
| `POST /leads` | `POST` | Create a new lead. |
| `GET /leads/{id}` | `GET` | Retrieve single lead details, research facts, and touch history. |
| `POST /leads/{id}/run-pipeline` | `POST` | Trigger Research Agent + Drafting Agent + Genericness Checker. |
| `POST /leads/{id}/approve` | `POST` | Approve, edit, or reject a draft in Human Approval Queue with Guardrail checks. |
| `POST /leads/{id}/simulate-reply` | `POST` | Trigger Prospect Persona Reply Simulator (`eager_buyer`, `skeptic`, `out_of_office`, `hard_no`, `ghost`). |
| `POST /leads/{id}/classify-reply` | `POST` | Classify raw prospect reply text & execute next-step action. |
| `GET /guardrails/status` | `GET` | Retrieve daily send cap counter & suppression status. |
| `GET /suppression-list` | `GET` | List all suppressed emails/domains. |
| `POST /suppression-list` | `POST` | Add email or domain to suppression list. |
| `GET /decision-log` | `GET` | Global decision log feed (powers Live Reasoning Trace UI). |
| `GET /leads/{id}/decision-log` | `GET` | Retrieve decision logs specific to a lead. |
| `GET /analytics` | `GET` | Retrieve conversion funnel and reply rate analytics. |

---

## 🛡️ 5. Compulsory Features & Safety Guardrails

- [x] **Per-Lead Research Agent**: Pulls public news, funding, hiring, and role-change signals.
- [x] **Personalized Drafting**: Forces every draft to cite ≥2 inline research facts.
- [x] **Genericness Checker**: Automatically rejects generic drafts and retries with feedback.
- [x] **Human Approval Queue**: Nothing auto-sends without human operator review.
- [x] **Send Guardrails**: Daily send limit counter (`DAILY_SEND_CAP`) + Suppression List (Email & Domain level).
- [x] **Simulated Sandbox Inbox**: Writes sent emails to DB sandbox table (`simulated_inbox`) to guarantee no external email is ever contacted.
- [x] **Prospect Persona Simulator**: Roleplays 5 realistic prospect personas to demonstrate full loop live.
- [x] **5-Class Reply Intent Classifier**: `Interested`, `Objection`, `Out-of-Office`, `Not Interested`, `No Reply`.
- [x] **Webhook Escalation**: Sends instant alert notifications to Slack/Discord webhooks when leads show high buying intent.
- [x] **Explainable Decision Log**: Structured logging of input, reasoning, and output for every agent step.

---

## 📄 License

MIT License — Created for Capabl Agentic AI Saksham Hackathon.
