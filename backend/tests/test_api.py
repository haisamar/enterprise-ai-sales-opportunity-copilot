import os
os.environ["DATABASE_URL"] = "sqlite:///./test_copilot.db"
os.environ["COPILOT_MODE"] = "mock"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_analyze():
    payload = {
        "account_name": "Northstar Manufacturing (Synthetic)",
        "industry": "Manufacturing",
        "opportunity_context": "Sales leadership says opportunity preparation is inconsistent across complex enterprise accounts.",
        "business_objectives": "Improve discovery preparation and create a repeatable proof-of-value motion.",
        "known_constraints": "Customer data cannot be used for autonomous outreach; seller approval is mandatory.",
        "seller_notes": "Need a clear way to separate facts from assumptions."
    }
    created = client.post("/api/opportunities", json=payload)
    assert created.status_code == 200
    oid = created.json()["id"]
    analysis = client.post(f"/api/opportunities/{oid}/analyze")
    assert analysis.status_code == 200
    body = analysis.json()
    assert body["provider"] == "mock"
    assert "discovery_questions" in body["result"]
    assert body["human_reviewed"] is False
