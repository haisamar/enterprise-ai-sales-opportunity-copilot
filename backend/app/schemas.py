from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


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
    human_reviewed: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
