import datetime
import logging
from sqlalchemy.orm import Session
from app.models import Lead, ResearchFact, Touch, DecisionLog, Reply, SimulatedInbox, ClassifierFeedback
from app.services.guardrails import GuardrailsService
from app.services.webhook import WebhookService
from app.agents.state import LeadState
from app.agents.graph import EchoReachGraphService

logger = logging.getLogger("echoreach.pipeline")

class AgentPipelineService:
    @staticmethod
    def _log_decision(db: Session, lead_id: int, agent_name: str, input_summary: str, reasoning: str, output_summary: str):
        log_entry = DecisionLog(
            lead_id=lead_id,
            agent_name=agent_name,
            input_summary=input_summary,
            reasoning=reasoning,
            output_summary=output_summary,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()

    @staticmethod
    def _sync_decision_traces(db: Session, lead_id: int, decision_trace: list):
        """Flushes in-memory LangGraph decision traces into the database decision_log table."""
        for trace in decision_trace:
            # Check if this exact entry is already logged
            existing = db.query(DecisionLog).filter(
                DecisionLog.lead_id == lead_id,
                DecisionLog.agent_name == trace["agent_name"],
                DecisionLog.input_summary == trace["input_summary"]
            ).first()
            if not existing:
                log_entry = DecisionLog(
                    lead_id=lead_id,
                    agent_name=trace["agent_name"],
                    input_summary=trace["input_summary"],
                    reasoning=trace["reasoning"],
                    output_summary=trace["output_summary"],
                    timestamp=datetime.datetime.utcnow()
                )
                db.add(log_entry)
        db.commit()

    @classmethod
    async def run_research_and_draft_graph(cls, db: Session, lead: Lead, touch_number: int = 1, channel: str = "email") -> tuple[list[ResearchFact], Touch]:
        """
        Executes the compiled LangGraph state machine:
        Research Agent -> Drafting Agent -> Genericness Checker (with Retry Loop)
        """
        initial_state: LeadState = {
            "lead_id": lead.id,
            "name": lead.name,
            "title": lead.title,
            "company": lead.company,
            "email": lead.email,
            "linkedin_url": lead.linkedin_url,
            "current_touch_number": touch_number,
            "channel": channel,
            "research_facts": [],
            "retry_count": 0,
            "decision_trace": []
        }

        # Run LangGraph State Machine
        final_state = await EchoReachGraphService.run_generation_pipeline(initial_state)

        # 1. Save extracted research facts to DB
        saved_facts = []
        for f in final_state.get("research_facts", []):
            rf = ResearchFact(
                lead_id=lead.id,
                fact_type=f.get("fact_type", "news"),
                content=f.get("content", ""),
                source=f.get("source"),
                kept_reason=f.get("kept_reason", "Key momentum signal")
            )
            db.add(rf)
            saved_facts.append(rf)

        # 2. Save generated touch draft to DB
        touch = Touch(
            lead_id=lead.id,
            touch_number=touch_number,
            channel=channel,
            subject=final_state.get("draft_subject", f"Outreach for {lead.company}"),
            body=final_state.get("draft_body", ""),
            status="pending_approval"
        )
        db.add(touch)

        lead.stage = "Pending Approval"
        db.commit()
        db.refresh(touch)

        # 3. Synchronize decision traces to database
        cls._sync_decision_traces(db, lead.id, final_state.get("decision_trace", []))

        return saved_facts, touch

    @classmethod
    async def run_research_agent(cls, db: Session, lead: Lead) -> list[ResearchFact]:
        """Direct Node 1 execution helper"""
        facts, _ = await cls.run_research_and_draft_graph(db, lead, touch_number=lead.current_touch_number)
        return facts

    @classmethod
    def run_drafting_agent(cls, db: Session, lead: Lead, touch_number: int = 1) -> Touch:
        """Helper to retrieve or generate draft"""
        touch = db.query(Touch).filter(Touch.lead_id == lead.id, Touch.touch_number == touch_number).order_by(Touch.id.desc()).first()
        return touch

    @classmethod
    def process_human_approval(cls, db: Session, touch: Touch, action: str, edited_subject: str = None, edited_body: str = None) -> tuple[bool, str]:
        """Node 4: Human Approval Queue & Guardrails Engine"""
        lead = db.query(Lead).filter(Lead.id == touch.lead_id).first()

        if action == "reject":
            touch.status = "rejected"
            lead.stage = "Draft Rejected"
            db.commit()
            cls._log_decision(
                db, lead_id=lead.id, agent_name="Human Guardrail Queue",
                input_summary=f"Human review for Touch #{touch.touch_number}",
                reasoning="Human operator rejected the draft.",
                output_summary="STATUS: REJECTED by human rep."
            )
            return True, "Draft rejected by operator."

        if action == "edit" and edited_body:
            touch.subject = edited_subject or touch.subject
            touch.body = edited_body

        # Check suppression list guardrail
        is_suppressed, supp_reason = GuardrailsService.check_suppression(db, lead.email)
        if is_suppressed:
            touch.status = "suppressed"
            lead.stage = "Stopped (Suppressed)"
            db.commit()
            cls._log_decision(
                db, lead_id=lead.id, agent_name="Send Guardrails Engine",
                input_summary=f"Send request for {lead.email}",
                reasoning=f"GUARDRAIL BLOCKED: {supp_reason}",
                output_summary="STATUS: BLOCKED BY SUPPRESSION LIST"
            )
            return False, f"Guardrail Alert: {supp_reason}"

        # Check daily send cap guardrail
        can_send, current_count, cap = GuardrailsService.check_daily_send_cap(db)
        if not can_send:
            touch.status = "cap_exceeded"
            db.commit()
            cls._log_decision(
                db, lead_id=lead.id, agent_name="Send Guardrails Engine",
                input_summary=f"Daily send cap check ({current_count}/{cap})",
                reasoning=f"GUARDRAIL BLOCKED: Daily send limit of {cap} reached.",
                output_summary="STATUS: BLOCKED BY DAILY SEND CAP"
            )
            return False, f"Guardrail Alert: Daily send cap ({cap}) reached for today."

        # Approve and send to Simulated Sandbox Inbox
        touch.status = "sent"
        touch.sent_at = datetime.datetime.utcnow()
        lead.stage = "Touch Sent"
        GuardrailsService.increment_daily_send_count(db)

        # Write entry to simulated inbox table
        inbox_entry = SimulatedInbox(
            lead_id=lead.id,
            touch_id=touch.id,
            channel=touch.channel,
            subject=touch.subject,
            body=touch.body,
            sent_at=touch.sent_at,
            status="Delivered"
        )
        db.add(inbox_entry)
        db.commit()

        cls._log_decision(
            db, lead_id=lead.id, agent_name="Human Guardrail Queue & Sandbox Sender",
            input_summary=f"Human approved Touch #{touch.touch_number}",
            reasoning=f"Passed all safety guardrails (Daily cap: {current_count+1}/{cap}, Suppression check: CLEAR). Written to Simulated Inbox.",
            output_summary="STATUS: APPROVED & DELIVERED TO SANDBOX INBOX"
        )
        return True, "Touch approved and delivered to simulated inbox."

    @classmethod
    async def process_reply_and_next_step(cls, db: Session, lead: Lead, raw_reply_text: str, persona_type: str = "custom") -> dict:
        """
        Executes the LangGraph Reply Loop:
        Reply Classifier (with Dynamic Few-Shot Feedback) -> Next-Step Decision Agent
        """
        initial_state: LeadState = {
            "lead_id": lead.id,
            "name": lead.name,
            "title": lead.title,
            "company": lead.company,
            "email": lead.email,
            "current_touch_number": lead.current_touch_number,
            "raw_reply_text": raw_reply_text,
            "persona_type": persona_type,
            "decision_trace": []
        }

        # Run LangGraph Reply Pipeline
        final_state = await EchoReachGraphService.run_reply_pipeline(initial_state, db_session=db)

        classification = final_state.get("reply_classification", "Interested")
        confidence = final_state.get("reply_confidence", 0.95)
        reasoning = final_state.get("reply_reasoning", "Evaluated intent.")
        next_step_action = final_state.get("next_step_action", "Execute Next Step")
        next_step_reason = final_state.get("next_step_reason", "Transitioned lead state.")

        # Record reply to database
        latest_touch = db.query(Touch).filter(Touch.lead_id == lead.id).order_by(Touch.id.desc()).first()
        touch_id = latest_touch.id if latest_touch else None

        reply_record = Reply(
            lead_id=lead.id,
            touch_id=touch_id,
            persona_type=persona_type,
            raw_text=raw_reply_text,
            classification=classification,
            confidence=confidence,
            reasoning=reasoning
        )
        db.add(reply_record)
        db.commit()

        # Execute DB transitions based on classification
        if classification == "Interested":
            lead.status = "Escalated"
            lead.stage = "Escalated to Rep"
            db.commit()

        elif classification == "Objection":
            lead.status = "Active"
            lead.stage = "Objection Drafted"
            db.commit()
            
            # Auto-draft objection handling follow-up touch
            objection_touch = Touch(
                lead_id=lead.id,
                touch_number=lead.current_touch_number + 1,
                channel="email",
                subject=f"Re: Integration & Workflow details for {lead.company}",
                body=f"Hi {lead.name},\n\nThanks for bringing that up! EchoReach integrates seamlessly with existing CRMs via native REST APIs without creating data silos.\n\nWould you like me to send over our 2-page integration guide?",
                status="pending_approval"
            )
            db.add(objection_touch)
            db.commit()

        elif classification == "Out-of-Office":
            lead.status = "Paused"
            lead.stage = "Paused (OOO)"
            db.commit()

        elif classification == "Not Interested":
            lead.status = "Stopped"
            lead.stage = "Stopped (Not Interested)"
            db.commit()

        else: # No Reply
            if lead.current_touch_number < 4:
                lead.current_touch_number += 1
                lead.stage = f"Cadence Touch #{lead.current_touch_number}"
                db.commit()
            else:
                lead.status = "Completed"
                lead.stage = "Sequence Completed"
                db.commit()

        # Flush decision traces into database
        cls._sync_decision_traces(db, lead.id, final_state.get("decision_trace", []))

        return {
            "classification": classification,
            "confidence": confidence,
            "next_step_action": next_step_action,
            "reasoning": next_step_reason
        }
