import os

os.environ["DATABASE_URL"] = "sqlite:///./test_copilot.db"
os.environ["COPILOT_MODE"] = "mock"
os.environ["WATSONX_API_KEY"] = ""
os.environ["WATSONX_PROJECT_ID"] = ""
os.environ["WATSONX_URL"] = ""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PAYLOAD = {
    "account_name": "Northstar Manufacturing (Synthetic)",
    "industry": "Manufacturing",
    "opportunity_context": "Preparation is inconsistent across complex enterprise accounts.",
    "business_objectives": "Create a repeatable proof-of-value motion.",
    "known_constraints": "Seller approval is mandatory.",
    "seller_notes": "Keep facts and hypotheses separate.",
}


def test_invalid_model_response_is_not_persisted(monkeypatch):
    def fake_generate(_data):
        return {"not": "a brief"}, 12, "watsonx.ai", "ibm/granite-4-h-small"

    def fake_repair(_invalid, _errors):
        return {"still": "invalid"}, 4

    monkeypatch.setattr("app.services.agent.generate_brief", fake_generate)
    monkeypatch.setattr("app.services.agent.repair_brief", fake_repair)
    created = client.post("/api/opportunities", json=PAYLOAD)
    assert created.status_code == 200
    analysis = client.post(f"/api/opportunities/{created.json()['id']}/analyze")
    assert analysis.status_code == 422
    detail = analysis.json()["detail"]
    assert detail["stage"] == "validate"
    assert detail["provider_attempted"] == "watsonx.ai"
    assert detail["validation_errors"]
