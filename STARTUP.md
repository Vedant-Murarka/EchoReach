# EchoReach — Quickstart, Testing & Execution Guide

This document provides exact, copy-paste instructions to set up, run, test, and demonstrate **EchoReach**.

---

## ⚡ 1. Prerequisites

- **Python 3.10+** installed
- A command terminal (PowerShell, Command Prompt, or Bash)

---

## 🛠️ 2. Environment Setup (One-Time)

### Step 1: Open Terminal in Project Directory
```powershell
cd c:\Coding\EchoReach
```

### Step 2: Create and Activate Virtual Environment
**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure API Keys (Optional)
The `.env` file is pre-configured. If you have API keys, add them into `.env`:
- **Gemini**: `GEMINI_API_KEY=...` (Free tier from [Google AI Studio](https://aistudio.google.com))
- **Groq**: `GROQ_API_KEY=...` (Free tier from [Groq Console](https://console.groq.com))
- **Supabase**: `DATABASE_URL=postgresql://postgres:...` (Free tier from [Supabase](https://supabase.com))

*(Note: EchoReach has built-in heuristic fallback, so it runs smoothly even with zero API keys!)*

---

## 🧪 3. Running Automated Tests

Run the complete Pytest test suite (all 13 tests covering the 6-agent LangGraph state machine, genericness checker retry loop, self-improving classifier memory, and API endpoints):

```powershell
.\venv\Scripts\pytest -v
```

Expected output:
```text
tests/test_agents_langgraph.py::test_research_agent_node PASSED          [  7%]
tests/test_agents_langgraph.py::test_drafting_agent_fact_citation PASSED [ 15%]
tests/test_agents_langgraph.py::test_genericness_checker_evaluation PASSED [ 23%]
tests/test_agents_langgraph.py::test_sequence_planner_cadence PASSED     [ 30%]
tests/test_agents_langgraph.py::test_reply_classifier_5_classes PASSED   [ 38%]
tests/test_agents_langgraph.py::test_next_step_decision_actions PASSED   [ 46%]
tests/test_agents_langgraph.py::test_langgraph_full_generation_graph PASSED [ 53%]
tests/test_agents_langgraph.py::test_self_improving_classifier_correction_api PASSED [ 61%]
tests/test_backend.py::test_root_health PASSED                           [ 69%]
tests/test_backend.py::test_create_and_get_lead PASSED                   [ 76%]
tests/test_backend.py::test_guardrail_suppression PASSED                 [ 84%]
tests/test_backend.py::test_simulate_reply_and_next_step PASSED          [ 92%]
tests/test_backend.py::test_analytics_endpoint PASSED                    [100%]

======================= 13 passed in 2.17s =======================
```

---

## 🚀 4. Seeding Dataset & Running Live Demos

### Step 1: Seed Synthetic Pipeline Data
Populate 15 synthetic leads, research signals, suppression list rules, and classifier few-shot memory:
```powershell
.\venv\Scripts\python seed_data.py
```

### Step 2: Run Full Terminal Demo Loop
Run the complete 6-step lifecycle in your terminal (Research $\rightarrow$ Draft $\rightarrow$ Genericness Check $\rightarrow$ Approval $\rightarrow$ Sandbox Send $\rightarrow$ Prospect Reply Simulator $\rightarrow$ Intent Classification $\rightarrow$ Decision Trace):
```powershell
.\venv\Scripts\python demo_run.py
```

---

## 🌐 5. Starting the FastAPI Server

Launch the REST API server:
```powershell
.\venv\Scripts\uvicorn app.main:app --reload --port 8000
```

- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: 👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
- **OpenAPI JSON Schema**: `http://127.0.0.1:8000/openapi.json`

---

## 📡 6. Key REST Endpoints to Demo

| Endpoint | Method | Purpose |
|---|---|---|
| `/leads` | `GET` | Retrieve pipeline leads filterable by stage |
| `/leads/{id}/run-pipeline` | `POST` | Trigger LangGraph Research + Drafting + Genericness retry loop |
| `/leads/{id}/approve` | `POST` | Approve, edit, or reject draft with send cap + suppression checks |
| `/leads/{id}/simulate-reply` | `POST` | Simulate prospect reply persona (`eager_buyer`, `skeptic`, etc.) |
| `/replies/{id}/correct` | `POST` | **Self-Improving Classifier**: submit operator correction for dynamic few-shot training |
| `/decision-log` | `GET` | Global real-time reasoning trace of all agent decisions |
| `/guardrails/status` | `GET` | Daily send cap usage counter and suppression list statistics |
| `/analytics` | `GET` | Funnel metrics, reply rates, and classification breakdown |
