import os

os.environ["DATABASE_URL"] = "sqlite:///./test_copilot.db"
os.environ["COPILOT_MODE"] = "mock"
os.environ["WATSONX_API_KEY"] = ""
os.environ["WATSONX_PROJECT_ID"] = ""
os.environ["WATSONX_URL"] = ""

import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.brief_schema import format_validation_errors, validate_brief
from app.db import SessionLocal
from app.main import app
from app.models import AnalysisRun
from app.services.copilot import apply_fact_grounding, mock_analysis
from app.services.watsonx import WatsonxError, extract_json

client = TestClient(app)

DATA = {
    "account_name": "Northstar Manufacturing (Synthetic)",
    "industry": "Manufacturing",
    "website": "",
    "opportunity_context": "Sales leadership says opportunity preparation is inconsistent.",
    "business_objectives": "Improve discovery preparation.",
    "known_constraints": "Seller approval is mandatory.",
    "seller_notes": "Separate facts from assumptions.",
}

PAYLOAD = {
    "account_name": DATA["account_name"],
    "industry": DATA["industry"],
    "opportunity_context": DATA["opportunity_context"],
    "business_objectives": DATA["business_objectives"],
    "known_constraints": DATA["known_constraints"],
    "seller_notes": DATA["seller_notes"],
}


def test_valid_granite_shaped_json():
    brief = validate_brief(mock_analysis(DATA))
    assert brief.account_context.unknowns
    assert brief.personalized_outreach.conversation_angle


def test_fenced_json_extracts():
    payload = {"account_summary": "ok"}
    raw = "```json\n" + json.dumps(payload) + "\n```"
    assert extract_json(raw) == payload
    assert extract_json("```\n" + json.dumps(payload) + "\n```") == payload


def test_missing_required_field():
    with pytest.raises(ValidationError) as exc:
        validate_brief({"account_summary": "x"})
    errors = format_validation_errors(exc.value)
    assert any(item["field"] == "account_context" for item in errors)


def test_wrong_nested_type():
    with pytest.raises(ValidationError) as exc:
        validate_brief({"account_context": "not-an-object"})
    errors = format_validation_errors(exc.value)
    assert errors[0]["field"] == "account_context"
    assert errors[0]["received_type"] == "str"


def test_truncated_invalid_json():
    with pytest.raises(WatsonxError) as exc:
        extract_json('{"account_context": {"facts": [')
    assert exc.value.stage == "parse"


def test_repair_succeeds_and_grounds_facts(monkeypatch):
    invalid = {"account_summary": "model invented a $1B customer"}
    valid = mock_analysis(DATA)

    def fake_generate(_data):
        return invalid, 80, "watsonx.ai", "ibm/granite-4-h-small"

    def fake_repair(payload, errors):
        assert payload == invalid
        assert errors
        valid["account_context"]["facts"] = ["Invented customer revenue is $1B"]
        return valid, 40

    monkeypatch.setattr("app.services.agent.generate_brief", fake_generate)
    monkeypatch.setattr("app.services.agent.repair_brief", fake_repair)
    created = client.post("/api/opportunities", json=PAYLOAD)
    analysis = client.post(f"/api/opportunities/{created.json()['id']}/analyze")
    assert analysis.status_code == 200
    body = analysis.json()
    assert body["provider"] == "watsonx.ai"
    assert body["model_id"] == "ibm/granite-4-h-small"
    assert body["repair_attempted"] is True
    facts = " ".join(body["result"]["account_context"]["facts"])
    assert "Invented customer revenue" not in facts
    assert "Northstar Manufacturing" in facts


def test_repair_fails_twice_and_does_not_persist(monkeypatch):
    db = SessionLocal()
    before = db.query(AnalysisRun).count()
    db.close()

    def fake_generate(_data):
        return {"not": "valid"}, 10, "watsonx.ai", "ibm/granite-4-h-small"

    def fake_repair(_payload, _errors):
        return {"still": "invalid"}, 8

    monkeypatch.setattr("app.services.agent.generate_brief", fake_generate)
    monkeypatch.setattr("app.services.agent.repair_brief", fake_repair)
    created = client.post("/api/opportunities", json=PAYLOAD)
    analysis = client.post(f"/api/opportunities/{created.json()['id']}/analyze")
    assert analysis.status_code == 422
    detail = analysis.json()["detail"]
    assert detail["validation_errors"]
    assert any(item["field"] == "account_context" for item in detail["validation_errors"])
    db = SessionLocal()
    after = db.query(AnalysisRun).count()
    db.close()
    assert after == before


def test_grounding_after_valid_repair_payload():
    brief = validate_brief(mock_analysis(DATA))
    brief.account_context.facts = ["Invented customer fact"]
    grounded = apply_fact_grounding(brief, DATA)
    assert "Invented customer fact" not in grounded.account_context.facts
