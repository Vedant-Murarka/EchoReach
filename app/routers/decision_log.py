from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import DecisionLog
from app.schemas import DecisionLogSchema

router = APIRouter(tags=["Reasoning Trace & Decision Log"])

@router.get("/decision-log", response_model=List[DecisionLogSchema])
def get_global_decision_log(limit: int = Query(default=50, le=200), db: Session = Depends(get_db)):
    """
    Returns global agent decision log feed to power Member C's Live Reasoning Trace UI panel.
    """
    return db.query(DecisionLog).order_by(DecisionLog.id.desc()).limit(limit).all()

@router.get("/leads/{lead_id}/decision-log", response_model=List[DecisionLogSchema])
def get_lead_decision_log(lead_id: int, db: Session = Depends(get_db)):
    return db.query(DecisionLog).filter(DecisionLog.lead_id == lead_id).order_by(DecisionLog.id.asc()).all()
