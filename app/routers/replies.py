from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Lead
from app.schemas import SimulateReplyRequest, ClassifyReplyRequest
from app.services.simulator import ProspectSimulatorService
from app.services.agent_pipeline import AgentPipelineService

router = APIRouter(prefix="/leads", tags=["Prospect Reply Simulation & Intent"])

@router.post("/{lead_id}/simulate-reply")
async def simulate_prospect_reply(lead_id: int, req: SimulateReplyRequest, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")

    simulated = ProspectSimulatorService.generate_simulated_reply(req.persona_type, lead.name, lead.company)
    
    # Immediately process reply through classifier & next-step decision agent
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

@router.post("/{lead_id}/classify-reply")
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
