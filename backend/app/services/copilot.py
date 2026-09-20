import time

from ..brief_schema import OpportunityBrief, validate_brief
from ..config import settings
from ..prompts import build_repair_prompt, build_system_prompt, build_user_prompt
from .watsonx import WatsonxClient, WatsonxError

PROVIDER_MOCK = "local_mock"
PROVIDER_WATSONX = "watsonx.ai"
MOCK_MODEL_ID = "deterministic-interview-demo"

DISPLAY_PROVIDERS = {
    PROVIDER_MOCK: "Local deterministic demo",
    PROVIDER_WATSONX: "IBM watsonx.ai",
}


def load_account_context(data: dict) -> dict:
    return {
        "account_name": data.get("account_name") or "",
        "industry": data.get("industry") or "",
        "website": data.get("website") or "",
        "opportunity_context": data.get("opportunity_context") or "",
        "business_objectives": data.get("business_objectives") or "",
        "known_constraints": data.get("known_constraints") or "",
        "seller_notes": data.get("seller_notes") or "",
    }


def ground_facts(data: dict) -> list[str]:
    facts = []
    if data.get("account_name"):
        facts.append(f"Account name supplied by seller: {data['account_name']}")
    if data.get("industry"):
        facts.append(f"Industry supplied by seller: {data['industry']}")
    if data.get("website"):
        facts.append(f"Website supplied by seller: {data['website']}")
    if data.get("opportunity_context"):
        facts.append(f"Seller-provided opportunity context: {data['opportunity_context']}")
    if data.get("business_objectives"):
        facts.append(f"Seller-provided business objectives: {data['business_objectives']}")
    if data.get("known_constraints"):
        facts.append(f"Seller-provided known constraints: {data['known_constraints']}")
    if data.get("seller_notes"):
        facts.append(f"Seller-provided notes: {data['seller_notes']}")
    return facts


def apply_fact_grounding(brief: OpportunityBrief, data: dict) -> OpportunityBrief:
    payload = brief.model_dump()
    payload["account_context"]["facts"] = ground_facts(data)
    if not payload.get("account_summary"):
        payload["account_summary"] = (
            f"{data.get('account_name') or 'Unnamed account'}"
            f"{' — ' + data['industry'] if data.get('industry') else ''}"
        )
    if not payload.get("success_criteria") and payload.get("proof_of_value", {}).get("success_metrics"):
        payload["success_criteria"] = payload["proof_of_value"]["success_metrics"]
    risks = list(payload.get("risks_and_open_questions") or [])
    for item in payload.get("solution_hypotheses") or []:
        risks.extend(item.get("risks") or [])
    risks.extend((payload.get("proof_of_value") or {}).get("risks") or [])
    risks.extend((payload.get("account_context") or {}).get("unknowns") or [])
    seen = set()
    unique = []
    for risk in risks:
        if risk and risk not in seen:
            seen.add(risk)
            unique.append(risk)
    payload["risks_and_open_questions"] = unique
    return validate_brief(payload)


def mock_analysis(data: dict) -> dict:
    constraint = data.get("known_constraints") or "No technical constraints supplied yet"
    return {
        "account_summary": f"{data.get('account_name')} — {data.get('industry') or 'industry not supplied'}",
        "account_context": {
            "facts": [],
            "unknowns": [
                "Named executive sponsor and economic buyer are not confirmed",
                "Current-state architecture and integration dependencies are not confirmed",
                "Baseline metrics for the business problem are not confirmed",
            ],
            "assumptions": [
                "Seller-supplied context is directionally accurate and still needs customer validation",
                "The account will permit a scoped proof of value before a broader rollout",
            ],
        },
        "stakeholder_hypotheses": [
            {
                "role": "Business owner / line-of-business leader",
                "likely_priorities": ["Business outcome", "Adoption", "Time to value"],
                "likely_concerns": ["Disruption to current process", "Unclear success measures"],
                "decision_influence": "Likely outcome owner; influence to be validated",
                "assumptions": ["A business owner exists and cares about preparation consistency"],
                "validation_question": "Who owns the business outcome and how is success measured today?",
            },
            {
                "role": "Technical decision maker",
                "likely_priorities": ["Integration", "Security", "Operability"],
                "likely_concerns": ["Uncontrolled AI output", "Mandatory architecture constraints"],
                "decision_influence": "Likely technical gatekeeper; influence to be validated",
                "assumptions": ["Technical approval is required before a proof of value"],
                "validation_question": "Which systems, security controls, and deployment constraints are non-negotiable?",
            },
        ],
        "business_problems": [
            {
                "problem": data.get("opportunity_context") or "Problem context not supplied",
                "evidence": "Seller-provided opportunity context; not independently verified with the customer",
                "confidence": "medium" if data.get("opportunity_context") else "low",
            }
        ],
        "discovery_questions": [
            {"category": "business", "question": "What business outcome is important enough to fund this initiative?", "why_it_matters": "Connects technical work to a measurable priority."},
            {"category": "value", "question": "What baseline metric should we compare against in a proof of value?", "why_it_matters": "Prevents an unmeasurable PoV."},
            {"category": "technical", "question": "Which systems and APIs must participate in the workflow?", "why_it_matters": "Identifies integration scope and feasibility."},
            {"category": "security", "question": "What data or actions would require additional approval or access controls?", "why_it_matters": "Surfaces governance constraints early."},
        ],
        "technical_constraints": [
            {
                "constraint": constraint,
                "status": "known" if data.get("known_constraints") else "unknown",
                "validation_question": "Which architecture, security, data-residency, or integration requirements are mandatory?",
            }
        ],
        "solution_hypotheses": [
            {
                "hypothesis": "Use an AI-assisted discovery workflow to structure account context, hypotheses, and proof-of-value planning while keeping the seller in control.",
                "customer_need": data.get("business_objectives") or "Business objective requires validation",
                "capability_needed": "Structured intake, enterprise model access, seller review, CRM-ready export",
                "assumptions": ["Customer permits use of selected account/opportunity data", "Seller validates generated hypotheses before use"],
                "risks": ["Hallucinated customer facts", "Incomplete discovery data", "Over-automation of seller judgment"],
            }
        ],
        "proof_of_value": {
            "hypothesis": "A structured AI-assisted discovery workflow can improve preparation quality without removing seller judgment.",
            "in_scope": ["One synthetic opportunity", "Discovery brief", "PoV success criteria", "CRM-ready summary"],
            "out_of_scope": ["Autonomous customer contact", "Pricing commitments", "Production CRM write-back"],
            "success_metrics": [
                {"metric": "Required discovery fields completed", "baseline_needed": "Current preparation process", "target_definition": "customer-agreed during discovery"},
                {"metric": "Generated claims correctly labelled as fact, hypothesis, or unknown", "baseline_needed": "Manual review checklist", "target_definition": "customer-agreed during discovery"},
            ],
            "data_requirements": ["Account context", "Opportunity notes", "Business objectives", "Known constraints"],
            "technical_validation": ["Structured JSON output", "Model-call trace captured", "Human review required"],
            "risks": ["Insufficient context", "Model output schema failure"],
        },
        "success_criteria": [
            {"metric": "Required discovery fields completed", "baseline_needed": "Current preparation process", "target_definition": "customer-agreed during discovery"},
            {"metric": "Generated claims correctly labelled as fact, hypothesis, or unknown", "baseline_needed": "Manual review checklist", "target_definition": "customer-agreed during discovery"},
        ],
        "business_value": {
            "value_drivers": ["Better-prepared discovery", "More consistent PoV framing", "Clearer handoff into CRM"],
            "assumptions_to_validate": ["Preparation inconsistency is a meaningful seller pain", "CRM brief format matches seller workflow"],
            "measurement_plan": ["Compare preparation completeness on the same synthetic scenario", "Review discovery-question relevance using a rubric"],
        },
        "risks_and_open_questions": [
            "Sponsor and economic buyer are unconfirmed",
            "Baseline metrics are unconfirmed",
        ],
        "crm_brief": {
            "customer_objective": data.get("business_objectives") or "To be validated in discovery",
            "problem_summary": data.get("opportunity_context") or "To be validated in discovery",
            "technical_summary": data.get("known_constraints") or "Technical constraints still need discovery",
            "next_best_discovery_step": "Validate business outcome, stakeholders, baseline metrics, and mandatory technical constraints before proposing a solution.",
        },
        "personalized_outreach": {
            "target_stakeholder": "Business owner / line-of-business leader",
            "relevant_business_issue": data.get("opportunity_context") or "Opportunity context requires validation",
            "conversation_angle": "Open with the seller-stated preparation inconsistency, then ask how discovery quality is judged today before discussing any solution.",
            "suggested_next_discovery_step": "Schedule a discovery conversation to confirm the outcome owner, baseline metric, and non-negotiable technical constraints.",
        },
    }


def generate_brief(data: dict) -> tuple[dict, int, str, str]:
    mode = settings.copilot_mode.lower().strip()
    if mode == "watsonx":
        try:
            result, latency = WatsonxClient().chat_json(build_system_prompt(), build_user_prompt(data))
        except WatsonxError:
            raise
        except Exception as exc:
            raise WatsonxError("watsonx", f"Unexpected watsonx.ai failure: {exc}") from exc
        return result, latency, PROVIDER_WATSONX, settings.watsonx_model_id
    result = mock_analysis(data)
    started = time.perf_counter()
    latency = int((time.perf_counter() - started) * 1000)
    return result, latency, PROVIDER_MOCK, MOCK_MODEL_ID


def repair_brief(invalid_json: dict, validation_errors: list[dict]) -> tuple[dict, int]:
    try:
        return WatsonxClient().chat_json(
            "You repair JSON for a schema-constrained enterprise discovery brief. Return one JSON object only.",
            build_repair_prompt(invalid_json, validation_errors),
            max_completion_tokens=6000,
        )
    except WatsonxError:
        raise
    except Exception as exc:
        raise WatsonxError("watsonx", f"Unexpected watsonx.ai repair failure: {exc}") from exc
