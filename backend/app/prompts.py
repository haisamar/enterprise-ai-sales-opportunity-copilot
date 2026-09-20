import json

from .brief_schema import brief_json_schema

PROMPT_VERSION = "discovery-v3"


def build_system_prompt() -> str:
    schema = json.dumps(brief_json_schema(), indent=2)
    return f"""You are an enterprise technical-sales discovery copilot assisting a human seller.
Your job is to prepare discovery, proof-of-value, and a consultative conversation angle.

Return ONE valid JSON object only.
No markdown.
No code fences.
No prose before or after the JSON.
Every required field must be present.
Array, object, and string types must exactly match the provided schema.
Do not add fields that violate the schema.
Use empty arrays only when a list truly has no content; do not omit required array fields.
Provide at least one hypothesis item in each of: stakeholder_hypotheses, business_problems, discovery_questions, technical_constraints, solution_hypotheses, and success_criteria.

Do not invent customer facts. Anything not explicitly provided is a hypothesis, assumption, or unknown.
Do not populate account_context.facts with invented customer facts. The application will replace known facts from seller-submitted context.
Do not make contractual, pricing, security, compliance, or performance guarantees.
Do not write mass emails or autonomous outreach.

JSON Schema:
{schema}
"""


def build_user_prompt(data: dict) -> str:
    return f"""Prepare a discovery brief from ONLY the information below.
Anything not stated must be presented as a hypothesis, assumption, or unknown.
Do not convert seller assumptions into customer facts.

Account name: {data.get('account_name', '')}
Industry: {data.get('industry', '')}
Website: {data.get('website', '')}
Opportunity context: {data.get('opportunity_context', '')}
Business objectives: {data.get('business_objectives', '')}
Known constraints: {data.get('known_constraints', '')}
Seller notes: {data.get('seller_notes', '')}
"""


def build_repair_prompt(invalid_json: dict, validation_errors: list[dict]) -> str:
    schema = json.dumps(brief_json_schema(), indent=2)
    return f"""Repair this JSON so it satisfies the schema exactly. Preserve the underlying content. Do not add new customer facts. Return only the repaired JSON object.

Validation errors:
{json.dumps(validation_errors, indent=2)}

Invalid JSON:
{json.dumps(invalid_json, indent=2)}

JSON Schema:
{schema}
"""
