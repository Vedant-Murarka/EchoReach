from typing import TypedDict, List, Dict, Any, Optional
import datetime

class ResearchFactDict(TypedDict):
    fact_type: str # news, funding, hiring, role-change, product-launch
    content: str
    source: Optional[str]
    kept_reason: Optional[str]

class DecisionTraceEntry(TypedDict):
    agent_name: str
    input_summary: str
    reasoning: str
    output_summary: str
    timestamp: str

class LeadState(TypedDict, total=False):
    lead_id: int
    name: str
    title: str
    company: str
    email: str
    linkedin_url: Optional[str]
    
    current_touch_number: int
    channel: str # email, linkedin
    
    # Research Agent state
    research_query: str
    research_facts: List[Dict[str, Any]]
    
    # Drafting Agent state
    draft_subject: str
    draft_body: str
    draft_touch_id: Optional[int]
    
    # Genericness Checker state
    genericness_score: float
    genericness_passed: bool
    genericness_feedback: str
    retry_count: int
    
    # Human Approval & Guardrails state
    approval_status: str # pending_approval, approved, rejected, suppressed, cap_exceeded
    approval_message: str
    
    # Reply Simulation & Classifier state
    raw_reply_text: str
    persona_type: str
    reply_classification: str # Interested, Objection, Out-of-Office, Not Interested, No Reply
    reply_confidence: float
    reply_reasoning: str
    few_shot_examples_used: int
    
    # Next-Step Decision Agent state
    next_step_action: str
    next_step_reason: str
    
    # Audit & Reasoning Trace
    decision_trace: List[Dict[str, Any]]
    error: Optional[str]
