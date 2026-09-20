import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import Lead, Touch, ResearchFact, SuppressionList, DailySendCounter, Reply, ClassifierFeedback, DecisionLog
from app.agents.state import LeadState
from app.agents.research_agent import ResearchAgent
from app.agents.drafting_agent import DraftingAgent
from app.agents.genericness_checker import GenericnessCheckerAgent
from app.agents.sequence_planner import SequencePlannerAgent
from app.agents.reply_classifier import ReplyClassifierAgent
from app.agents.next_step_agent import NextStepDecisionAgent
from app.agents.graph import EchoReachGraphService

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.query(ClassifierFeedback).delete()
    db.query(Reply).delete()
    db.query(DecisionLog).delete()
    db.query(ResearchFact).delete()
    db.query(Touch).delete()
    db.query(Lead).delete()
    db.query(SuppressionList).delete()
    db.query(DailySendCounter).delete()
    db.commit()
    yield db
    db.close()

@pytest.mark.asyncio
async def test_research_agent_node():
    state: LeadState = {
        "lead_id": 1,
        "name": "Sarah Jenkins",
        "title": "VP of Revenue Operations",
        "company": "Apex Dynamics",
        "email": "sarah@apexdynamics.io",
        "decision_trace": []
    }
    result = await ResearchAgent.run(state)
    assert len(result["research_facts"]) >= 1
    assert "decision_trace" in result
    assert result["decision_trace"][0]["agent_name"] == "Research Agent"

@pytest.mark.asyncio
async def test_drafting_agent_fact_citation():
    state: LeadState = {
        "lead_id": 1,
        "name": "Sarah Jenkins",
        "title": "VP RevOps",
        "company": "Apex Dynamics",
        "email": "sarah@apexdynamics.io",
        "current_touch_number": 1,
        "channel": "email",
        "research_facts": [
            {"fact_type": "funding", "content": "Apex raised $18M Series B", "kept_reason": "Growth signal"},
            {"fact_type": "hiring", "content": "Apex is scaling sales ops team", "kept_reason": "Hiring momentum"}
        ],
        "decision_trace": []
    }
    result = await DraftingAgent.run(state)
    assert len(result["draft_body"]) > 30
    assert "Sarah" in result["draft_body"]

@pytest.mark.asyncio
async def test_genericness_checker_evaluation():
    # Good draft with fact citations
    state_good: LeadState = {
        "company": "Apex Dynamics",
        "draft_body": "Hi Sarah, I saw that Apex raised $18M Series B and is actively scaling its sales ops team. Let's talk.",
        "research_facts": [
            {"fact_type": "funding", "content": "Apex raised $18M Series B"},
            {"fact_type": "hiring", "content": "Apex is actively scaling its sales ops team"}
        ],
        "retry_count": 0,
        "decision_trace": []
    }
    res_good = await GenericnessCheckerAgent.run(state_good)
    assert res_good["genericness_passed"] is True
    assert res_good["genericness_score"] >= 0.8

    # Generic draft with banned phrase
    state_bad: LeadState = {
        "company": "Apex Dynamics",
        "draft_body": "Hope this email finds you well! Quick question about synergy.",
        "research_facts": [],
        "retry_count": 0,
        "decision_trace": []
    }
    res_bad = await GenericnessCheckerAgent.run(state_bad)
    assert res_bad["genericness_passed"] is False

def test_sequence_planner_cadence():
    state: LeadState = {
        "current_touch_number": 1,
        "reply_classification": "No Reply",
        "decision_trace": []
    }
    res = SequencePlannerAgent.run(state)
    assert res["current_touch_number"] == 2
    assert res["channel"] in ["email", "linkedin"]

@pytest.mark.asyncio
async def test_reply_classifier_5_classes():
    # Interested
    res1 = await ReplyClassifierAgent.run({"raw_reply_text": "Sounds great, send me your calendar link!", "decision_trace": []})
    assert res1["reply_classification"] == "Interested"

    # Out-of-Office
    res2 = await ReplyClassifierAgent.run({"raw_reply_text": "I am out of the office until Monday.", "decision_trace": []})
    assert res2["reply_classification"] == "Out-of-Office"

    # Not Interested
    res3 = await ReplyClassifierAgent.run({"raw_reply_text": "Please remove me from your list. Unsubscribe.", "decision_trace": []})
    assert res3["reply_classification"] == "Not Interested"

    # Objection
    res4 = await ReplyClassifierAgent.run({"raw_reply_text": "We already use ZoomInfo and Outreach, how do you integrate?", "decision_trace": []})
    assert res4["reply_classification"] == "Objection"

@pytest.mark.asyncio
async def test_next_step_decision_actions():
    # Interested -> Escalate
    res_interested = await NextStepDecisionAgent.run({
        "reply_classification": "Interested",
        "name": "Sarah",
        "company": "Apex",
        "decision_trace": []
    })
    assert "Escalate" in res_interested["next_step_action"]

    # Objection -> Draft Objection Touch
    res_objection = await NextStepDecisionAgent.run({
        "reply_classification": "Objection",
        "name": "Sarah",
        "company": "Apex",
        "decision_trace": []
    })
    assert "Objection" in res_objection["next_step_action"]

    # OOO -> Pause
    res_ooo = await NextStepDecisionAgent.run({
        "reply_classification": "Out-of-Office",
        "name": "Sarah",
        "company": "Apex",
        "decision_trace": []
    })
    assert "Pause" in res_ooo["next_step_action"]

    # Not Interested -> Stop
    res_stop = await NextStepDecisionAgent.run({
        "reply_classification": "Not Interested",
        "name": "Sarah",
        "company": "Apex",
        "decision_trace": []
    })
    assert "Stop" in res_stop["next_step_action"]

@pytest.mark.asyncio
async def test_langgraph_full_generation_graph():
    initial_state: LeadState = {
        "lead_id": 1,
        "name": "Alex Dubois",
        "title": "VP of Demand Gen",
        "company": "Synthetix AI",
        "email": "alex@synthetix.ai",
        "current_touch_number": 1,
        "channel": "email",
        "research_facts": [],
        "retry_count": 0,
        "decision_trace": []
    }
    final_state = await EchoReachGraphService.run_generation_pipeline(initial_state)
    assert len(final_state["research_facts"]) >= 1
    assert len(final_state["draft_body"]) > 20
    assert len(final_state["decision_trace"]) >= 2

def test_self_improving_classifier_correction_api(clean_db):
    # Create lead and simulate reply
    lead_resp = client.post("/leads", json={
        "name": "Elena Rostova",
        "title": "Director",
        "company": "CloudForge",
        "email": "elena@cloudforge.ai"
    }).json()
    lead_id = lead_resp["id"]

    sim_resp = client.post(f"/leads/{lead_id}/simulate-reply", json={"persona_type": "skeptic"}).json()
    
    # Fetch replies
    replies_resp = client.get("/replies").json()
    assert len(replies_resp) >= 1
    reply_id = replies_resp[0]["id"]

    # Submit operator correction
    correct_resp = client.post(f"/replies/{reply_id}/correct", json={
        "corrected_classification": "Objection",
        "notes": "Reclassified by human reviewer"
    })
    assert correct_resp.status_code == 200
    assert correct_resp.json()["status"] == "success"

    # Check feedback history
    fb_resp = client.get("/replies/feedback").json()
    assert len(fb_resp) >= 1
    assert fb_resp[0]["corrected_class"] == "Objection"
