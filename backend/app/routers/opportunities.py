from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AnalysisRun, CrmExportEvent, Opportunity
from ..schemas import AnalysisOut, CrmExportOut, OpportunityCreate, OpportunityOut, ReviewIn
from ..services.agent import BriefValidationError, OpportunityCopilotAgent
from ..services.watsonx import WatsonxError

router = APIRouter(prefix="/api", tags=["opportunities"])
agent = OpportunityCopilotAgent()


def _error_payload(message: str, stage: str, provider=None, model_id=None, validation_errors=None):
    payload = {
        "error": message,
        "stage": stage,
        "provider_attempted": provider,
        "model_attempted": model_id,
    }
    if validation_errors is not None:
        payload["validation_errors"] = validation_errors
    return payload


@router.post("/opportunities", response_model=OpportunityOut)
def create_opportunity(payload: OpportunityCreate, db: Session = Depends(get_db)):
    row = Opportunity(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/opportunities", response_model=list[OpportunityOut])
def list_opportunities(db: Session = Depends(get_db)):
    return db.scalars(select(Opportunity).order_by(Opportunity.id.desc())).all()


@router.post("/opportunities/{opportunity_id}/analyze", response_model=AnalysisOut)
def analyze_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    row = db.get(Opportunity, opportunity_id)
    if not row:
        raise HTTPException(404, "Opportunity not found")
    try:
        return agent.run(row, db)
    except BriefValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=_error_payload(
                str(exc),
                exc.stage,
                exc.provider,
                exc.model_id,
                exc.validation_errors,
            ),
        ) from exc
    except WatsonxError as exc:
        raise HTTPException(
            status_code=502,
            detail=_error_payload(exc.message, exc.stage, "watsonx.ai", None),
        ) from exc


@router.get("/analysis/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    run = db.get(AnalysisRun, analysis_id)
    if not run:
        raise HTTPException(404, "Analysis run not found")
    return run


@router.post("/analysis/{analysis_id}/review", response_model=AnalysisOut)
def review_analysis(analysis_id: int, payload: ReviewIn, db: Session = Depends(get_db)):
    run = db.get(AnalysisRun, analysis_id)
    if not run:
        raise HTTPException(404, "Analysis run not found")
    run.review_status = payload.status
    run.review_note = payload.note
    db.commit()
    db.refresh(run)
    return run


@router.get("/analysis/{analysis_id}/export")
def export_analysis(analysis_id: int, db: Session = Depends(get_db)):
    run = db.get(AnalysisRun, analysis_id)
    if not run:
        raise HTTPException(404, "Analysis run not found")
    body = {
        "analysis_id": run.id,
        "opportunity_id": run.opportunity_id,
        "review_status": run.review_status,
        "review_note": run.review_note,
        "provider": run.provider,
        "model_id": run.model_id,
        "prompt_version": run.prompt_version,
        "latency_ms": run.latency_ms,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "result": run.result,
    }
    return JSONResponse(body)


@router.post("/analysis/{analysis_id}/crm-export", response_model=CrmExportOut)
def crm_export(analysis_id: int, db: Session = Depends(get_db)):
    run = db.get(AnalysisRun, analysis_id)
    if not run:
        raise HTTPException(404, "Analysis run not found")
    if run.review_status != "approved":
        raise HTTPException(409, "CRM-ready export is blocked until the seller approves the brief.")
    payload = {
        "event": "opportunity.brief.approved",
        "source": "enterprise-ai-sales-opportunity-copilot",
        "mode": "simulated_webhook",
        "opportunity_id": run.opportunity_id,
        "analysis_id": run.id,
        "review_status": run.review_status,
        "provider": run.provider,
        "model_id": run.model_id,
        "crm_brief": (run.result or {}).get("crm_brief", {}),
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    event = CrmExportEvent(
        analysis_id=run.id,
        opportunity_id=run.opportunity_id,
        payload=payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
