from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Lead, Reply, ClassifierFeedback
from app.schemas import (
    SimulateReplyRequest, ClassifyReplyRequest,
    ClassifierCorrectionRequest, ClassifierFeedbackSchema, ReplySchema
)
from app.services.simulator import ProspectSimulatorService
from app.services.agent_pipeline import AgentPipelineService

router = APIRouter(tags=["Prospect Reply Simulation & Self-Improving Classifier"])

@router.post("/leads/{lead_id}/simulate-reply")
async def simulate_prospect_reply(lead_id: int, req: SimulateReplyRequest, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")

    simulated = ProspectSimulatorService.generate_simulated_reply(req.persona_type, lead.name, lead.company)
    
    # Process reply through LangGraph classifier & next-step decision agent
    pipeline_result = await AgentPipelineService.process_reply_and_next_step(
        db, lead, simulated["raw_text"], persona_type=simulated["persona_type"]
    )

    return {
        "lead_id": lead.id,
        "persona_type": simulated["persona_type"],
        "simulated_reply": simulated["raw_text"],
        "classification": pipeline_result["classification"],
        "confidence": pipeline_result["confidence"],
        "next_step_action": pipeline_result["next_step_action"],
        "reasoning": pipeline_result["reasoning"]
    }

@router.post("/leads/{lead_id}/classify-reply")
async def classify_raw_reply(lead_id: int, req: ClassifyReplyRequest, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")

    pipeline_result = await AgentPipelineService.process_reply_and_next_step(
        db, lead, req.raw_reply_text, persona_type="custom_user_input"
    )

    return {
        "lead_id": lead.id,
        "classification": pipeline_result["classification"],
        "confidence": pipeline_result["confidence"],
        "next_step_action": pipeline_result["next_step_action"],
        "reasoning": pipeline_result["reasoning"]
    }

@router.get("/replies", response_model=List[ReplySchema])
def get_all_replies(db: Session = Depends(get_db)):
    return db.query(Reply).order_by(Reply.id.desc()).all()

@router.post("/replies/{reply_id}/correct")
def submit_classifier_correction(reply_id: int, req: ClassifierCorrectionRequest, db: Session = Depends(get_db)):
    """
    Self-Improving Classifier Endpoint:
    Stores operator correction into classifier_feedback table to be injected as dynamic few-shot training exemplars.
    """
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found.")

    old_class = reply.classification
    reply.is_corrected = 1
    reply.corrected_classification = req.corrected_classification

    feedback_entry = ClassifierFeedback(
        reply_id=reply.id,
        raw_text=reply.raw_text,
        predicted_class=old_class,
        corrected_class=req.corrected_classification,
        notes=req.notes
    )
    db.add(feedback_entry)
    db.commit()
    db.refresh(feedback_entry)

    AgentPipelineService._log_decision(
        db,
        lead_id=reply.lead_id,
        agent_name="Self-Improving Classifier Engine",
        input_summary=f"Operator correction for Reply #{reply.id}",
        reasoning=f"Human operator reclassified from '{old_class}' to '{req.corrected_classification}'. Saved to dynamic few-shot exemplars memory.",
        output_summary=f"RECLASSIFIED: {req.corrected_classification}"
    )

    return {
        "status": "success",
        "message": f"Correction recorded. Future classifications will utilize this exemplar.",
        "feedback_id": feedback_entry.id,
        "previous_classification": old_class,
        "new_classification": req.corrected_classification
    }

@router.get("/replies/feedback", response_model=List[ClassifierFeedbackSchema])
def get_classifier_feedback_history(db: Session = Depends(get_db)):
    """Lists human corrections used for self-improving few-shot injection."""
    return db.query(ClassifierFeedback).order_by(ClassifierFeedback.id.desc()).all()
