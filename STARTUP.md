# EchoReach — Quickstart, Testing & Execution Guide

This document provides exact, step-by-step instructions to run, test, and demonstrate **EchoReach**.

---

## ⚡ 1. Prerequisites

- **Python 3.10+** installed
- Terminal (PowerShell or Command Prompt on Windows, or Bash on macOS/Linux)

---

## 🛠️ 2. Environment Setup

### Step 1: Open Terminal in Project Root
```powershell
cd c:\Coding\EchoReach
```

### Step 2: Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
.\venv\Scripts\activate
```

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Environment Variables (`.env`)
The `.env` file is pre-configured with Supabase, Groq, Gemini, and Serper API keys.
> [!TIP]
> If your Supabase password contains an `@` sign, it is automatically URL-encoded as `%40` in `app/database.py` to prevent URI parsing errors!

---

## 🧪 3. Running Automated Tests (100% Passing)

Run the automated test suite covering all 6 LangGraph agent nodes, the genericness retry loop, self-improving classifier few-shot memory, and API endpoints:

```powershell
.\venv\Scripts\pytest -v
```

*Expected Output:*
```text
============================= test session starts =============================
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
====================== 13 passed in 23s =======================
```

---

## 🚀 4. Seeding Dataset & Terminal Demo

### Step 1: Seed Supabase / Local Database
Populates 15 synthetic leads, research signals, suppression rules, and classifier few-shot exemplars:
```powershell
.\venv\Scripts\python seed_data.py
```

### Step 2: Run Full Terminal Demo Loop
Executes the full 6-agent lifecycle (Research $\rightarrow$ Draft $\rightarrow$ Genericness Check $\rightarrow$ Approval $\rightarrow$ Sandbox Send $\rightarrow$ Reply Simulation $\rightarrow$ Intent Classification $\rightarrow$ Decision Trace):
```powershell
.\venv\Scripts\python demo_run.py
```

---

## 🌐 5. Launching the Interactive Frontend & API Server

### Option A: Using the Quick-Launch Script (Recommended)
**Double-click** or run:
```powershell
.\start.ps1
```
or in CMD:
```cmd
start.bat
```

### Option B: Using Uvicorn Directly
```powershell
.\venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🖥️ 6. Using the Interactive Dashboard

Open your browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

### Dashboard Features Available:
1. **📊 Pipeline Board**: View all leads across stages (`New`, `Researched`, `Pending Approval`, `Touch Sent`, `Escalated to Rep`, `Stopped`). Click **"Run Graph"** on any lead to trigger the live LangGraph agent.
2. **🛡️ Human Approval Queue**: Side-by-side view of extracted research facts, generated drafts, guardrail checks (Daily Cap & Suppression), and `Approve`, `Edit`, or `Reject` actions.
3. **🧠 Live Reasoning Trace**: Real-time agent-to-agent decision stream with agent avatars, inputs, step-by-step reasoning, and outcomes.
4. **🎭 Reply Simulator**: Pick a lead, select a persona (`Eager Buyer`, `Skeptic`, `Out of Office`, `Hard No`, `Ghost`), and trigger the 5-class intent classifier and next-step action in real time.
5. **✏️ Self-Improving Studio**: Submit human operator corrections for any reply. Corrections are stored in the database and automatically injected as dynamic few-shot training exemplars into future classification calls!
6. **📈 Analytics**: Real-time pipeline stage funnel and reply rate distribution charts.

---

## 📡 7. Interactive API Explorer (OpenAPI / Swagger)

Navigate to:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
Test every REST endpoint directly in your browser.
