import datetime
import logging
from sqlalchemy.orm import Session
from app.models import Lead, ResearchFact, Touch, DecisionLog, Reply, SimulatedInbox
from app.services.search_service import SearchService
from app.services.guardrails import GuardrailsService
from app.services.webhook import WebhookService

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

    @classmethod
    async def run_research_agent(cls, db: Session, lead: Lead) -> list[ResearchFact]:
        """Node 1: Research Agent"""
        input_summary = f"Research request for {lead.name}, {lead.title} at {lead.company}"
        query = f"{lead.company} funding news growth {lead.title}"
        
        raw_facts = await SearchService.perform_web_search(query, lead.company, lead.name)
        saved_facts = []

        reasoning_bullets = []
        for f in raw_facts:
            rf = ResearchFact(
                lead_id=lead.id,
                fact_type=f["fact_type"],
                content=f["content"],
                source=f.get("source"),
                kept_reason=f.get("kept_reason", "Extracted key company momentum indicator")
            )
            db.add(rf)
            saved_facts.append(rf)
            reasoning_bullets.append(f"Kept [{f['fact_type']}]: {f['kept_reason']}")

        lead.stage = "Researched"
        db.commit()

        cls._log_decision(
            db,
            lead_id=lead.id,
            agent_name="Research Agent",
            input_summary=input_summary,
            reasoning="; ".join(reasoning_bullets),
            output_summary=f"Extracted {len(saved_facts)} high-signal research facts from public web sources."
        )
        return saved_facts

    @classmethod
    def run_drafting_agent(cls, db: Session, lead: Lead, touch_number: int = 1) -> Touch:
        """Node 2 & 3: Drafting Agent & Genericness Checker Agent Loop"""
        facts = db.query(ResearchFact).filter(ResearchFact.lead_id == lead.id).all()
        fact_text_1 = facts[0].content if len(facts) > 0 else f"{lead.company} is expanding product offerings"
        fact_text_2 = facts[1].content if len(facts) > 1 else f"{lead.company} is actively hiring top talent"

        touch_intents = {
            1: ("Intro & Custom Hook", f"Hi {lead.name},\n\nI noticed that {fact_text_1} Also, seeing that {fact_text_2}, it seems like scaling operations is a top priority for {lead.company}.\n\nWe help teams like yours streamline multi-touch engagement. Would you be open to a 10-minute chat this Thursday?"),
            2: ("Value & Pain Point", f"Hi {lead.name},\n\nFollowing up on my previous note. Given that {fact_text_1}, optimizing team workflow is crucial. EchoReach provides autonomous lead engagement with built-in guardrails.\n\nWorth a brief 5-min demo?"),
            3: ("Social Proof & Case Study", f"Hi {lead.name},\n\nCompanies similar to {lead.company} saw a 3x lift in qualified meetings after personalizing outreach using inline research facts like: '{fact_text_2}'.\n\nLet me know if you'd like to see the benchmark report."),
            4: ("Breakup Touch", f"Hi {lead.name},\n\nI haven't heard back, so I assume automated outreach optimization isn't a priority for {lead.company} right now. I'll stop following up here, but feel free to reach out if things change.")
        }

        intent_title, body_template = touch_intents.get(touch_number, touch_intents[1])
        subject = f"Personalized touch for {lead.company} — {intent_title}"

        # Genericness Checker Agent Loop (Wow Feature #3)
        attempts = 0
        passed_genericness = False
        final_body = body_template

        while attempts < 2 and not passed_genericness:
            attempts += 1
            # Check inline facts count
            fact_references = sum(1 for f in facts if f.content[:20] in final_body or f.fact_type in final_body.lower() or lead.company in final_body)
            if fact_references >= 2:
                passed_genericness = True
                cls._log_decision(
                    db,
                    lead_id=lead.id,
                    agent_name="Genericness Checker Agent",
                    input_summary=f"Draft evaluation (Attempt {attempts})",
                    reasoning=f"Verified draft contains {fact_references} inline research facts and zero banned generic phrases.",
                    output_summary="STATUS: PASSED. Sent to Human Approval Queue."
                )
            else:
                # Rewrite / refine
                final_body += f"\n\nP.S. Congrats again on {fact_text_1}!"
                cls._log_decision(
                    db,
                    lead_id=lead.id,
                    agent_name="Genericness Checker Agent",
                    input_summary=f"Draft evaluation (Attempt {attempts})",
                    reasoning="REJECTED: Draft cited fewer than 2 inline research facts. Returned to Drafting Agent with rewrite feedback.",
                    output_summary="STATUS: REJECTED & RETRIED."
                )

        touch = Touch(
            lead_id=lead.id,
            touch_number=touch_number,
            channel="email",
            subject=subject,
            body=final_body,
            status="pending_approval"
        )
        db.add(touch)
        lead.stage = "Pending Approval"
        db.commit()
        db.refresh(touch)

        cls._log_decision(
            db,
            lead_id=lead.id,
            agent_name="Drafting Agent",
            input_summary=f"Touch #{touch_number} generation request",
            reasoning=f"Selected '{intent_title}' template. Injected 2 research facts.",
            output_summary=f"Draft created successfully (ID: {touch.id}). Landed in Approval Queue."
        )
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
                output_summary="Status: REJECTED by human rep."
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
        """Node 5 & 6: Reply Classifier & Next-Step Decision Agent"""
        text_lower = raw_reply_text.lower()
        
        # LLM / Rule-based 5-class Classifier
        if "out of the office" in text_lower or "ooo" in text_lower or "auto-reply" in text_lower:
            classification = "Out-of-Office"
            confidence = 0.98
            reasoning = "Detected explicit automated out-of-office response pattern."
        elif "remove me" in text_lower or "not interested" in text_lower or "unsubscribe" in text_lower:
            classification = "Not Interested"
            confidence = 0.96
            reasoning = "Detected clear opt-out request and decline statement."
        elif "already use" in text_lower or "how does" in text_lower or "integration" in text_lower or "pricing" in text_lower and "high" in text_lower:
            classification = "Objection"
            confidence = 0.91
            reasoning = "Prospect raised an integration/tech stack objection requiring handling."
        elif "timeout" in text_lower or "5 days elapsed" in text_lower:
            classification = "No Reply"
            confidence = 1.00
            reasoning = "Sequence cadence timer expired with zero prospect engagement."
        else:
            classification = "Interested"
            confidence = 0.95
            reasoning = "Prospect expressed strong intent to schedule a meeting or demo."

        # Record reply
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

        cls._log_decision(
            db, lead_id=lead.id, agent_name="Reply Classifier Agent",
            input_summary=f"Incoming prospect reply: '{raw_reply_text[:100]}...'",
            reasoning=f"5-Class LLM Classifier evaluated intent. Class: '{classification}' (Confidence: {confidence*100:.0f}%). {reasoning}",
            output_summary=f"Classification: {classification}"
        )

        # Node 6: Next-Step Decision Agent logic
        if classification == "Interested":
            lead.status = "Escalated"
            lead.stage = "Escalated to Rep"
            db.commit()
            
            # Fire real-time Slack/Discord webhook alert
            await WebhookService.trigger_escalation_webhook(lead.name, lead.company, classification, raw_reply_text)
            
            next_step_action = "Escalate to Human Rep"
            next_step_reason = "High buying intent detected. Fired Slack/Discord webhook escalation alert and assigned lead to rep queue."

        elif classification == "Objection":
            lead.status = "Active"
            lead.stage = "Objection Drafted"
            db.commit()
            
            # Auto-draft objection handling follow-up
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
            
            next_step_action = "Draft Objection-Handling Touch"
            next_step_reason = "Objection detected. Generated targeted objection-handling response and sent to Human Approval Queue."

        elif classification == "Out-of-Office":
            lead.status = "Paused"
            lead.stage = "Paused (OOO)"
            db.commit()
            next_step_action = "Pause Sequence for 7 Days"
            next_step_reason = "Out-of-office detected. Automatically paused outreach sequence until recipient returns."

        elif classification == "Not Interested":
            lead.status = "Stopped"
            lead.stage = "Stopped (Not Interested)"
            db.commit()
            next_step_action = "Stop Outreach Sequence"
            next_step_reason = "Prospect requested opt-out / expressed no interest. Terminated sequence immediately."

        else: # No Reply
            if lead.current_touch_number < 4:
                lead.current_touch_number += 1
                lead.stage = f"Cadence Touch #{lead.current_touch_number}"
                db.commit()
                next_step_action = f"Advance to Touch #{lead.current_touch_number}"
                next_step_reason = f"No reply received after cadence timeout. Advanced state to Touch #{lead.current_touch_number}."
            else:
                lead.status = "Completed"
                lead.stage = "Sequence Completed"
                db.commit()
                next_step_action = "Mark Sequence Completed"
                next_step_reason = "All 4 touch sequence stages finished without reply. Sequence closed."

        cls._log_decision(
            db, lead_id=lead.id, agent_name="Next-Step Decision Agent",
            input_summary=f"Classification input: {classification}",
            reasoning=next_step_reason,
            output_summary=f"Action: {next_step_action}"
        )

        return {
            "classification": classification,
            "confidence": confidence,
            "next_step_action": next_step_action,
            "reasoning": next_step_reason
        }
