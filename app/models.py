import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    title = Column(String(100), nullable=False)
    company = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    linkedin_url = Column(String(255), nullable=True)
    
    # Stages: New -> Researched -> Drafted -> Pending Approval -> Approved -> Sent -> Replied -> Escalated / Stopped
    stage = Column(String(50), default="New", index=True)
    current_touch_number = Column(Integer, default=1)
    status = Column(String(50), default="Active") # Active, Paused, Escalated, Stopped, Completed
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    research_facts = relationship("ResearchFact", back_populates="lead", cascade="all, delete-orphan")
    touches = relationship("Touch", back_populates="lead", cascade="all, delete-orphan")
    decision_logs = relationship("DecisionLog", back_populates="lead", cascade="all, delete-orphan")
    replies = relationship("Reply", back_populates="lead", cascade="all, delete-orphan")

class ResearchFact(Base):
    __tablename__ = "research_facts"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    fact_type = Column(String(50), nullable=False) # news, funding, hiring, role-change, product-launch
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    kept_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    lead = relationship("Lead", back_populates="research_facts")

class Touch(Base):
    __tablename__ = "touches"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    touch_number = Column(Integer, nullable=False)
    channel = Column(String(50), default="email") # email, linkedin
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    
    # Status: draft, pending_approval, approved, rejected, sent
    status = Column(String(50), default="pending_approval", index=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    lead = relationship("Lead", back_populates="touches")
    simulated_inbox_entries = relationship("SimulatedInbox", back_populates="touch", cascade="all, delete-orphan")

class DecisionLog(Base):
    __tablename__ = "decision_log"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    agent_name = Column(String(100), nullable=False, index=True)
    input_summary = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=False)
    output_summary = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    lead = relationship("Lead", back_populates="decision_logs")

class SuppressionList(Base):
    __tablename__ = "suppression_list"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=True)
    domain = Column(String(100), index=True, nullable=True)
    reason = Column(String(255), default="User requested opt-out")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SimulatedInbox(Base):
    __tablename__ = "simulated_inbox"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    touch_id = Column(Integer, ForeignKey("touches.id"), nullable=False)
    channel = Column(String(50), default="email")
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="Delivered")

    touch = relationship("Touch", back_populates="simulated_inbox_entries")

class Reply(Base):
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    touch_id = Column(Integer, ForeignKey("touches.id"), nullable=True)
    persona_type = Column(String(50), nullable=False) # Eager Buyer, Skeptic, Out-of-Office, Hard No, Ghost
    raw_text = Column(Text, nullable=False)
    
    # Classification: Interested, Objection, Out-of-Office, Not Interested, No Reply
    classification = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.95)
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    lead = relationship("Lead", back_populates="replies")

class DailySendCounter(Base):
    __tablename__ = "daily_send_counter"

    id = Column(Integer, primary_key=True, index=True)
    date_str = Column(String(20), unique=True, index=True, nullable=False)
    send_count = Column(Integer, default=0)
    daily_cap = Column(Integer, default=50)
