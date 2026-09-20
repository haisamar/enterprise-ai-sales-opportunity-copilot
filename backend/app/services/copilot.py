import time
from ..config import settings
from ..prompts import SYSTEM_PROMPT, build_user_prompt
from .watsonx import WatsonxClient


def mock_analysis(data: dict) -> tuple[dict, int]:
    started = time.perf_counter()
    result = {
        "account_context": {
            "facts": [
                f"Account: {data['account_name']}",
                f"Industry supplied by seller: {data.get('industry') or 'not provided'}",
                f"Business objective supplied: {data.get('business_objectives') or 'not provided'}",
            ],
            "unknowns": [
                "Executive sponsor and economic buyer",
                "Current-state architecture and integration dependencies",
                "Baseline metrics for the business problem",
            ],
        },
        "stakeholder_hypotheses": [
            {
                "persona": "Business owner / line-of-business leader",
                "likely_priorities": ["Business outcome", "adoption", "time to value"],
                "validate_with_customer": ["Who owns the outcome?", "How is success measured today?"],
            },
            {
                "persona": "Technical decision maker",
                "likely_priorities": ["integration", "security", "operability"],
                "validate_with_customer": ["What systems must the solution integrate with?", "What deployment constraints are non-negotiable?"],
            },
        ],
        "business_problems": [
            {
                "problem": data.get("opportunity_context") or "Problem context not supplied",
                "evidence": "Seller-provided opportunity context",
                "confidence": "medium",
            }
        ],
        "discovery_questions": [
            {"category": "business", "question": "What business outcome is important enough to fund this initiative?", "why_it_matters": "Connects the technical work to a measurable priority."},
            {"category": "value", "question": "What baseline metric should we compare against in a proof of value?", "why_it_matters": "Prevents an unmeasurable PoV."},
            {"category": "technical", "question": "Which systems and APIs must participate in the workflow?", "why_it_matters": "Identifies integration scope and feasibility."},
            {"category": "security", "question": "What data or actions would require additional approval or access controls?", "why_it_matters": "Surfaces governance constraints early."},
        ],
        "technical_constraints": [
            {"constraint": data.get("known_constraints") or "No technical constraints supplied yet", "status": "known" if data.get("known_constraints") else "unknown", "validation_question": "Which architecture, security, data-residency, or integration requirements are mandatory?"}
        ],
        "solution_hypotheses": [
            {
                "hypothesis": "Use an AI-assisted workflow to structure discovery inputs and proof-of-value planning while keeping the seller in control.",
                "customer_need": data.get("business_objectives") or "Business objective requires validation",
                "capability_needed": "Structured intake, enterprise AI reasoning, seller review, API integration",
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
                {"metric": "Generated claims correctly labelled as fact/hypothesis/unknown", "baseline_needed": "Manual review checklist", "target_definition": "customer-agreed during discovery"},
            ],
            "data_requirements": ["Account context", "Opportunity notes", "Business objectives", "Known constraints"],
            "technical_validation": ["Structured JSON output", "Model-call trace captured", "Human review required"],
            "risks": ["Insufficient context", "Model output schema failure", "Sensitive-data leakage if data controls are ignored"],
        },
        "business_value": {
            "value_drivers": ["Better-prepared discovery", "More consistent PoV framing", "Clearer handoff into CRM"],
            "assumptions_to_validate": ["Preparation inconsistency is a meaningful seller pain", "CRM brief format matches seller workflow"],
            "measurement_plan": ["Compare preparation completeness on the same synthetic scenario", "Review discovery-question relevance using a rubric"],
        },
        "crm_brief": {
            "customer_objective": data.get("business_objectives") or "To be validated in discovery",
            "problem_summary": data.get("opportunity_context") or "To be validated in discovery",
            "technical_summary": data.get("known_constraints") or "Technical constraints still need discovery",
            "next_best_discovery_step": "Validate business outcome, stakeholders, baseline metrics, and mandatory technical constraints before proposing a solution.",
        },
    }
    return result, int((time.perf_counter() - started) * 1000)


def analyze(data: dict) -> tuple[dict, int, str, str]:
    if settings.copilot_mode.lower() == "watsonx":
        result, latency = WatsonxClient().chat_json(SYSTEM_PROMPT, build_user_prompt(data))
        return result, latency, "watsonx.ai", settings.watsonx_model_id
    result, latency = mock_analysis(data)
    return result, latency, "mock", "deterministic-interview-demo"
