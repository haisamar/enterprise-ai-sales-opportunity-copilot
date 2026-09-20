import os

os.environ["DATABASE_URL"] = "sqlite:///./test_copilot.db"
os.environ["COPILOT_MODE"] = "mock"
os.environ["WATSONX_API_KEY"] = ""
os.environ["WATSONX_PROJECT_ID"] = ""
os.environ["WATSONX_URL"] = ""

from fastapi.testclient import TestClient

from app.brief_schema import validate_brief
from app.db import Base, engine
from app.main import app
from app.services.copilot import apply_fact_grounding, ground_facts, mock_analysis

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)

PAYLOAD = {
    "account_name": "Northstar Manufacturing (Synthetic)",
    "industry": "Manufacturing",
    "opportunity_context": "Sales leadership says opportunity preparation is inconsistent across complex enterprise accounts.",
    "business_objectives": "Improve discovery preparation and create a repeatable proof-of-value motion.",
    "known_constraints": "Customer data cannot be used for autonomous outreach; seller approval is mandatory.",
    "seller_notes": "Need a clear way to separate facts from assumptions.",
}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["review_required"] is True


def test_create_and_analyze_mock():
    created = client.post("/api/opportunities", json=PAYLOAD)
    assert created.status_code == 200
    opportunity_id = created.json()["id"]
    analysis = client.post(f"/api/opportunities/{opportunity_id}/analyze")
    assert analysis.status_code == 200
    body = analysis.json()
    assert body["provider"] == "local_mock"
    assert body["model_id"] == "deterministic-interview-demo"
    assert body["review_status"] == "pending"
    result = body["result"]
    for key in [
        "account_summary",
        "account_context",
        "stakeholder_hypotheses",
        "business_problems",
        "discovery_questions",
        "technical_constraints",
        "solution_hypotheses",
        "proof_of_value",
        "success_criteria",
        "business_value",
        "risks_and_open_questions",
        "crm_brief",
        "personalized_outreach",
    ]:
        assert key in result
    facts = " ".join(result["account_context"]["facts"])
    assert "Northstar Manufacturing" in facts
    assert result["account_context"]["unknowns"]
    assert result["stakeholder_hypotheses"][0]["role"]


def test_missing_opportunity():
    response = client.post("/api/opportunities/99999/analyze")
    assert response.status_code == 404


def test_ai_status_and_ping_without_credentials():
    status = client.get("/api/ai/status")
    assert status.status_code == 200
    assert status.json()["credentials_present"] is False
    ping = client.post("/api/ai/ping")
    assert ping.status_code == 200
    body = ping.json()
    assert body["connected"] is False
    assert body["stage"] == "config"
    assert "WATSONX_API_KEY" in body["error"]
    assert "access_token" not in str(body).lower()
    assert "apikey" not in str(body).lower()


def test_review_and_crm_export_gate():
    created = client.post("/api/opportunities", json=PAYLOAD).json()
    analysis = client.post(f"/api/opportunities/{created['id']}/analyze").json()
    analysis_id = analysis["id"]
    blocked = client.post(f"/api/analysis/{analysis_id}/crm-export")
    assert blocked.status_code == 409
    revised = client.post(
        f"/api/analysis/{analysis_id}/review",
        json={"status": "needs_revision", "note": "Check sponsor"},
    )
    assert revised.status_code == 200
    assert revised.json()["review_status"] == "needs_revision"
    still_blocked = client.post(f"/api/analysis/{analysis_id}/crm-export")
    assert still_blocked.status_code == 409
    approved = client.post(
        f"/api/analysis/{analysis_id}/review",
        json={"status": "approved", "note": "Seller reviewed"},
    )
    assert approved.status_code == 200
    assert approved.json()["review_status"] == "approved"
    exported = client.post(f"/api/analysis/{analysis_id}/crm-export")
    assert exported.status_code == 200
    payload = exported.json()["payload"]
    assert payload["event"] == "opportunity.brief.approved"
    assert payload["mode"] == "simulated_webhook"
    download = client.get(f"/api/analysis/{analysis_id}/export")
    assert download.status_code == 200
    assert download.json()["result"]["crm_brief"]
