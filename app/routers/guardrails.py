from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import SuppressionList
from app.schemas import GuardrailStatusResponse, SuppressionCreate, SuppressionResponse
from app.services.guardrails import GuardrailsService

router = APIRouter(tags=["Safety & Guardrails"])

@router.get("/guardrails/status", response_model=GuardrailStatusResponse)
def get_guardrail_status(db: Session = Depends(get_db)):
    return GuardrailsService.get_guardrail_status(db)

@router.get("/suppression-list", response_model=List[SuppressionResponse])
def get_suppression_list(db: Session = Depends(get_db)):
    return db.query(SuppressionList).order_by(SuppressionList.id.desc()).all()

@router.post("/suppression-list", response_model=SuppressionResponse)
def add_to_suppression_list(req: SuppressionCreate, db: Session = Depends(get_db)):
    if not req.email and not req.domain:
        raise HTTPException(status_code=400, detail="Must provide either an email or domain to suppress.")
    
    entry = SuppressionList(
        email=req.email.lower() if req.email else None,
        domain=req.domain.lower() if req.domain else None,
        reason=req.reason or "Manual opt-out"
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
