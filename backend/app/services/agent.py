import logging

from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..brief_schema import format_validation_errors, validate_brief
from ..models import AnalysisRun
from ..prompts import PROMPT_VERSION
from .copilot import PROVIDER_WATSONX, apply_fact_grounding, generate_brief, load_account_context, repair_brief

logger = logging.getLogger("copilot.agent")


class BriefValidationError(ValueError):
    def __init__(self, message: str, provider: str, model_id: str, validation_errors: list[dict] | None = None):
        super().__init__(message)
        self.provider = provider
        self.model_id = model_id
        self.stage = "validate"
        self.validation_errors = validation_errors or []


class OpportunityCopilotAgent:
    """Bounded opportunity-analysis agent: load → generate → validate → ground facts → persist."""

    def run(self, opportunity, db: Session) -> AnalysisRun:
        context = load_account_context({
            "account_name": opportunity.account_name,
            "industry": opportunity.industry,
            "website": opportunity.website,
            "opportunity_context": opportunity.opportunity_context,
            "business_objectives": opportunity.business_objectives,
            "known_constraints": opportunity.known_constraints,
            "seller_notes": opportunity.seller_notes,
        })
        raw, latency, provider, model_id = generate_brief(context)
        repair_attempted = False
        brief = None
        try:
            brief = validate_brief(raw)
        except ValidationError as first_error:
            errors = format_validation_errors(first_error)
            logger.info("brief_validation_failed provider=%s errors=%s", provider, errors)
            if provider != PROVIDER_WATSONX:
                raise BriefValidationError(
                    "Generated output failed schema validation",
                    provider=provider,
                    model_id=model_id,
                    validation_errors=errors,
                ) from first_error
            repair_attempted = True
            logger.info("granite_repair_attempted=true")
            repaired, repair_latency = repair_brief(raw, errors)
            latency += repair_latency
            try:
                brief = validate_brief(repaired)
            except ValidationError as second_error:
                second_errors = format_validation_errors(second_error)
                logger.info("brief_repair_failed errors=%s", second_errors)
                raise BriefValidationError(
                    "Generated output failed schema validation",
                    provider=provider,
                    model_id=model_id,
                    validation_errors=second_errors,
                ) from second_error
        grounded = apply_fact_grounding(brief, context)
        run = AnalysisRun(
            opportunity_id=opportunity.id,
            prompt_version=PROMPT_VERSION,
            provider=provider,
            model_id=model_id,
            latency_ms=latency,
            result=grounded.model_dump(),
            review_status="pending",
            review_note="",
            fallback_used=False,
            repair_attempted=repair_attempted,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
