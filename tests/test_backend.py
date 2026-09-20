import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import Lead, Touch, SuppressionList, DailySendCounter

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Clear test data
    db.query(Touch).delete()
    db.query(Lead).delete()
    db.query(SuppressionList).delete()
    db.query(DailySendCounter).delete()
    db.commit()
    yield
    db.close()

def test_root_health():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_create_and_get_lead():
    payload = {
        "name": "Test User",
        "title": "Director of Sales",
        "company": "TestCorp",
        "email": "test.user@testcorp.com",
        "linkedin_url": "https://linkedin.com/in/testuser"
    }
    create_resp = client.post("/leads", json=payload)
    assert create_resp.status_code == 200
    data = create_resp.json()
    assert data["name"] == "Test User"
    assert data["stage"] == "New"

    get_resp = client.get("/leads")
    assert get_resp.status_code == 200
    assert len(get_resp.json()) == 1

def test_guardrail_suppression():
    # Add email to suppression list
    supp_resp = client.post("/suppression-list", json={"email": "blocked@suppressed.com", "reason": "Opt out"})
    assert supp_resp.status_code == 200

    status_resp = client.get("/guardrails/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["suppressed_emails_count"] >= 1

def test_simulate_reply_and_next_step():
    # Create lead
    payload = {"name": "Demo Lead", "title": "VP Growth", "company": "DemoInc", "email": "demo@demoinc.com"}
    lead_resp = client.post("/leads", json=payload).json()
    lead_id = lead_resp["id"]

    # Simulate reply
    sim_resp = client.post(f"/leads/{lead_id}/simulate-reply", json={"persona_type": "eager_buyer"})
    assert sim_resp.status_code == 200
    res = sim_resp.json()
    assert res["classification"] == "Interested"
    assert "Escalate" in res["next_step_action"]

def test_analytics_endpoint():
    resp = client.get("/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_leads" in data
    assert "reply_rate_percent" in data
