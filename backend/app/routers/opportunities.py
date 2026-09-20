from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import AnalysisRun, Opportunity
from ..prompts import PROMPT_VERSION
from ..schemas import AnalysisOut, OpportunityCreate, OpportunityOut
from ..services.copilot import analyze

router = APIRouter(prefix="/api", tags=["opportunities"])


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
    data = {k: getattr(row, k) for k in [
        "account_name", "industry", "website", "opportunity_context",
        "business_objectives", "known_constraints", "seller_notes"
    ]}
    result, latency, provider, model_id = analyze(data)
    run = AnalysisRun(
        opportunity_id=row.id,
        prompt_version=PROMPT_VERSION,
        provider=provider,
        model_id=model_id,
        latency_ms=latency,
        result=result,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/analysis/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    run = db.get(AnalysisRun, analysis_id)
    if not run:
        raise HTTPException(404, "Analysis run not found")
    return run


@router.post("/analysis/{analysis_id}/review", response_model=AnalysisOut)
def mark_reviewed(analysis_id: int, db: Session = Depends(get_db)):
    run = db.get(AnalysisRun, analysis_id)
    if not run:
        raise HTTPException(404, "Analysis run not found")
    run.human_reviewed = True
    db.commit()
    db.refresh(run)
    return run
