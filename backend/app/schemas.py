from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .brief_schema import OpportunityBrief


class OpportunityCreate(BaseModel):
    account_name: str = Field(min_length=2, max_length=180)
    industry: str = ""
    website: str = ""
    opportunity_context: str = Field(min_length=10)
    business_objectives: str = ""
    known_constraints: str = ""
    seller_notes: str = ""


class OpportunityOut(OpportunityCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AnalysisOut(BaseModel):
    id: int
    opportunity_id: int
    prompt_version: str
    provider: str
    model_id: str
    latency_ms: int
    result: dict
    review_status: str
    review_note: str = ""
    fallback_used: bool = False
    repair_attempted: bool = False
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReviewIn(BaseModel):
    status: Literal["approved", "needs_revision"]
    note: str = ""


class CrmExportOut(BaseModel):
    id: int
    analysis_id: int
    opportunity_id: int
    payload: dict
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AiStatusOut(BaseModel):
    copilot_mode: str
    credentials_present: bool
    provider_when_live: str = "watsonx.ai"
    model_id: str
    watsonx_url_configured: bool
    review_required: bool = True


class AiPingOut(BaseModel):
    connected: bool
    provider: str | None = None
    model_id: str | None = None
    base_url: str | None = None
    latency_ms: int | None = None
    stage: str
    error: str | None = None


class BriefValidationOut(BaseModel):
    brief: OpportunityBrief
