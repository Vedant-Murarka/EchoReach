from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime

class ResearchFactSchema(BaseModel):
    id: int
    fact_type: str
    content: str
    source: Optional[str] = None
    kept_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TouchSchema(BaseModel):
    id: int
    lead_id: int
    touch_number: int
    channel: str
    subject: Optional[str] = None
    body: str
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DecisionLogSchema(BaseModel):
    id: int
    lead_id: int
    agent_name: str
    input_summary: Optional[str] = None
    reasoning: str
    output_summary: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class ReplySchema(BaseModel):
    id: int
    lead_id: int
    touch_id: Optional[int] = None
    persona_type: str
    raw_text: str
    classification: str
    confidence: float
    reasoning: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LeadBase(BaseModel):
    name: str
    title: str
    company: str
    email: str
    linkedin_url: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadResponse(LeadBase):
    id: int
    stage: str
    current_touch_number: int
    status: str
    created_at: datetime
    updated_at: datetime
    research_facts: List[ResearchFactSchema] = []
    touches: List[TouchSchema] = []

    model_config = ConfigDict(from_attributes=True)

class DraftApprovalRequest(BaseModel):
    action: str  # "approve", "edit", "reject"
    edited_subject: Optional[str] = None
    edited_body: Optional[str] = None

class SimulateReplyRequest(BaseModel):
    persona_type: str # "eager_buyer", "skeptic", "out_of_office", "hard_no", "ghost"

class ClassifyReplyRequest(BaseModel):
    raw_reply_text: str

class SuppressionCreate(BaseModel):
    email: Optional[str] = None
    domain: Optional[str] = None
    reason: Optional[str] = "Manual opt-out"

class SuppressionResponse(BaseModel):
    id: int
    email: Optional[str] = None
    domain: Optional[str] = None
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class GuardrailStatusResponse(BaseModel):
    date: str
    send_count: int
    daily_cap: int
    remaining_sends: int
    suppressed_emails_count: int
    is_cap_reached: bool

class AnalyticsSummary(BaseModel):
    total_leads: int
    leads_by_stage: dict
    total_touches_sent: int
    replies_count: int
    reply_rate_percent: float
    replies_by_classification: dict
