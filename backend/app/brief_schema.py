from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator


Confidence = Literal["low", "medium", "high"]
ConstraintStatus = Literal["known", "hypothesis", "unknown"]


class AccountContext(BaseModel):
    facts: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class StakeholderHypothesis(BaseModel):
    role: str = ""
    likely_priorities: list[str] = Field(default_factory=list)
    likely_concerns: list[str] = Field(default_factory=list)
    decision_influence: str = ""
    assumptions: list[str] = Field(default_factory=list)
    validation_question: str = ""

    @field_validator("role", mode="before")
    @classmethod
    def coerce_role(cls, value):
        return value or ""


class BusinessProblem(BaseModel):
    problem: str
    evidence: str = ""
    confidence: Confidence = "low"


class DiscoveryQuestion(BaseModel):
    category: str
    question: str
    why_it_matters: str = ""


class TechnicalConstraint(BaseModel):
    constraint: str
    status: ConstraintStatus = "hypothesis"
    validation_question: str = ""


class SolutionHypothesis(BaseModel):
    hypothesis: str
    customer_need: str = ""
    capability_needed: str = ""
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class SuccessMetric(BaseModel):
    metric: str
    baseline_needed: str = ""
    target_definition: str = "customer-agreed during discovery"


class ProofOfValue(BaseModel):
    hypothesis: str = ""
    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    success_metrics: list[SuccessMetric] = Field(default_factory=list)
    data_requirements: list[str] = Field(default_factory=list)
    technical_validation: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class BusinessValue(BaseModel):
    value_drivers: list[str] = Field(default_factory=list)
    assumptions_to_validate: list[str] = Field(default_factory=list)
    measurement_plan: list[str] = Field(default_factory=list)


class CrmBrief(BaseModel):
    customer_objective: str = ""
    problem_summary: str = ""
    technical_summary: str = ""
    next_best_discovery_step: str = ""


class PersonalizedOutreach(BaseModel):
    target_stakeholder: str = ""
    relevant_business_issue: str = ""
    conversation_angle: str = ""
    suggested_next_discovery_step: str = ""


class OpportunityBrief(BaseModel):
    account_summary: str = ""
    account_context: AccountContext
    stakeholder_hypotheses: list[StakeholderHypothesis] = Field(default_factory=list)
    business_problems: list[BusinessProblem] = Field(default_factory=list)
    discovery_questions: list[DiscoveryQuestion] = Field(default_factory=list)
    technical_constraints: list[TechnicalConstraint] = Field(default_factory=list)
    solution_hypotheses: list[SolutionHypothesis] = Field(default_factory=list)
    proof_of_value: ProofOfValue = Field(default_factory=ProofOfValue)
    success_criteria: list[SuccessMetric] = Field(default_factory=list)
    business_value: BusinessValue = Field(default_factory=BusinessValue)
    risks_and_open_questions: list[str] = Field(default_factory=list)
    crm_brief: CrmBrief = Field(default_factory=CrmBrief)
    personalized_outreach: PersonalizedOutreach = Field(default_factory=PersonalizedOutreach)

    @field_validator("stakeholder_hypotheses", mode="before")
    @classmethod
    def normalize_stakeholders(cls, value):
        if not isinstance(value, list):
            return value
        normalized = []
        for item in value:
            if not isinstance(item, dict):
                normalized.append(item)
                continue
            row = dict(item)
            if not row.get("role") and row.get("persona"):
                row["role"] = row["persona"]
            if not row.get("validation_question"):
                questions = row.get("validate_with_customer") or []
                if questions:
                    row["validation_question"] = questions[0]
            normalized.append(row)
        return normalized


def brief_json_schema() -> dict:
    return OpportunityBrief.model_json_schema()


def format_validation_errors(exc: ValidationError) -> list[dict]:
    errors = []
    for item in exc.errors():
        received = item.get("input", _MISSING)
        entry = {
            "field": ".".join(str(part) for part in item.get("loc", [])),
            "message": item.get("msg", ""),
            "expected": item.get("type", ""),
        }
        if received is not _MISSING:
            entry["received_type"] = type(received).__name__
        errors.append(entry)
    return errors


def validate_brief(payload: dict) -> OpportunityBrief:
    return OpportunityBrief.model_validate(payload)


_MISSING = object()
