from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Lead, Touch, ResearchFact
from app.schemas import LeadResponse, LeadCreate, DraftApprovalRequest, TouchSchema
from app.services.agent_pipeline import AgentPipelineService

router = APIRouter(prefix="/leads", tags=["Leads & Pipeline"])

@router.get("", response_model=List[LeadResponse])
def get_leads(stage: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Lead)
    if stage:
        query = query.filter(Lead.stage == stage)
    return query.order_by(Lead.id.desc()).all()

@router.post("", response_model=LeadResponse)
def create_lead(lead_in: LeadCreate, db: Session = Depends(get_db)):
    existing = db.query(Lead).filter(Lead.email == lead_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Lead with this email already exists.")
    
    lead = Lead(
        name=lead_in.name,
        title=lead_in.title,
        company=lead_in.company,
        email=lead_in.email,
        linkedin_url=lead_in.linkedin_url,
        stage="New",
        current_touch_number=1,
        status="Active"
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead_by_id(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")
    return lead

@router.post("/{lead_id}/run-pipeline")
async def run_lead_pipeline(lead_id: int, touch_number: int = Query(default=1), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")
    
    # 1. Run Research Agent
    facts = await AgentPipelineService.run_research_agent(db, lead)
    
    # 2. Run Drafting Agent & Genericness Checker
    touch = AgentPipelineService.run_drafting_agent(db, lead, touch_number=touch_number)
    
    return {
        "status": "success",
        "lead_id": lead.id,
        "lead_stage": lead.stage,
        "facts_extracted": len(facts),
        "generated_touch_id": touch.id,
        "touch_status": touch.status
    }

@router.post("/{lead_id}/approve")
def approve_or_reject_draft(lead_id: int, touch_id: int, req: DraftApprovalRequest, db: Session = Depends(get_db)):
    touch = db.query(Touch).filter(Touch.id == touch_id, Touch.lead_id == lead_id).first()
    if not touch:
        raise HTTPException(status_code=404, detail="Touch draft not found.")
    
    success, message = AgentPipelineService.process_human_approval(
        db, touch, req.action, req.edited_subject, req.edited_body
    )
    
    return {
        "success": success,
        "message": message,
        "touch_id": touch.id,
        "touch_status": touch.status
    }
