import os

os.environ["DATABASE_URL"] = "sqlite:///./test_copilot.db"
os.environ["COPILOT_MODE"] = "mock"

import pytest
from pydantic import ValidationError

from app.brief_schema import validate_brief
from app.services.copilot import apply_fact_grounding, ground_facts, mock_analysis

DATA = {
    "account_name": "Northstar Manufacturing (Synthetic)",
    "industry": "Manufacturing",
    "website": "",
    "opportunity_context": "Sales leadership says opportunity preparation is inconsistent.",
    "business_objectives": "Improve discovery preparation.",
    "known_constraints": "Seller approval is mandatory.",
    "seller_notes": "Separate facts from assumptions.",
}


def test_schema_accepts_mock_output():
    brief = validate_brief(mock_analysis(DATA))
    assert brief.stakeholder_hypotheses
    assert brief.personalized_outreach.conversation_angle


def test_schema_rejects_invalid_output():
    with pytest.raises(ValidationError):
        validate_brief({"account_summary": "x"})


def test_known_facts_are_deterministic_and_not_model_authored():
    facts = ground_facts(DATA)
    assert any("Northstar Manufacturing" in item for item in facts)
    assert any("Seller-provided opportunity context" in item for item in facts)
    brief = validate_brief(mock_analysis(DATA))
    brief.account_context.facts = ["Invented customer revenue is $1B"]
    grounded = apply_fact_grounding(brief, DATA)
    joined = " ".join(grounded.account_context.facts)
    assert "Invented customer revenue" not in joined
    assert "Northstar Manufacturing" in joined
    assert grounded.account_context.unknowns
    assert grounded.account_context.assumptions
