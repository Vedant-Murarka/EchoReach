from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Lead, Touch, Reply
from app.schemas import AnalyticsSummary

router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])

@router.get("", response_model=AnalyticsSummary)
def get_analytics_summary(db: Session = Depends(get_db)):
    total_leads = db.query(Lead).count()
    
    # Stages aggregation
    stage_counts = db.query(Lead.stage, func.count(Lead.id)).group_by(Lead.stage).all()
    leads_by_stage = {stage: count for stage, count in stage_counts}

    total_touches_sent = db.query(Touch).filter(Touch.status == "sent").count()
    replies_count = db.query(Reply).count()
    
    reply_rate = round((replies_count / total_touches_sent * 100), 1) if total_touches_sent > 0 else 0.0

    # Classification breakdown
    class_counts = db.query(Reply.classification, func.count(Reply.id)).group_by(Reply.classification).all()
    replies_by_classification = {cls_name: count for cls_name, count in class_counts}

    return {
        "total_leads": total_leads,
        "leads_by_stage": leads_by_stage,
        "total_touches_sent": total_touches_sent,
        "replies_count": replies_count,
        "reply_rate_percent": reply_rate,
        "replies_by_classification": replies_by_classification
    }
