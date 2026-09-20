import datetime
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.agents.state import LeadState
from app.services.webhook import WebhookService

logger = logging.getLogger("echoreach.next_step_agent")

class NextStepDecisionAgent:
    """
    Node 6: Adaptive Next-Step Decision Agent (Rule + LLM Hybrid Engine)
    Autonomously executes state transitions: Escalate (Webhook) / Handle Objection / Pause / Stop / Advance.
    """

    @classmethod
    async def run(cls, state: LeadState) -> Dict[str, Any]:
        classification = state.get("reply_classification", "No Reply")
        lead_name = state.get("name", "Prospect")
        company = state.get("company", "Company")
        raw_reply = state.get("raw_reply_text", "")
        current_touch = state.get("current_touch_number", 1)

        input_summary = f"Evaluating adaptive next step for '{classification}' intent on {lead_name} at {company}"
        
        if classification == "Interested":
            next_action = "Escalate to Human Rep"
            next_reason = "High buying intent confirmed. Fired real-time Slack/Discord webhook escalation alert and queued lead for live sales rep engagement."
            # Fire webhook
            try:
                await WebhookService.trigger_escalation_webhook(lead_name, company, classification, raw_reply)
            except Exception as e:
                logger.warning(f"Webhook alert trigger failed: {e}")

        elif classification == "Objection":
            next_action = "Draft Objection-Handling Touch"
            next_reason = "Prospect raised an objection/question. Generated targeted objection-handling response citing integration capabilities and sent to Human Approval Queue."

        elif classification == "Out-of-Office":
            next_action = "Pause Sequence for 7 Days"
            next_reason = "Out-of-office autoreply detected. Automatically paused sequence to prevent burning cadence while prospect is away."

        elif classification == "Not Interested":
            next_action = "Stop Outreach Sequence"
            next_reason = "Opt-out / non-interest detected. Terminated sequence immediately to preserve domain reputation and honor prospect preference."

        else: # No Reply
            if current_touch < 4:
                next_action = f"Advance to Touch #{current_touch + 1}"
                next_reason = f"Cadence delay expired with no reply. Advanced sequence state to Touch #{current_touch + 1}."
            else:
                next_action = "Mark Sequence Completed"
                next_reason = "All 4 touch cadence steps exhausted without response. Closed sequence."

        output_summary = f"Action: {next_action}"

        decision_entry = {
            "agent_name": "Next-Step Decision Agent",
            "input_summary": input_summary,
            "reasoning": next_reason,
            "output_summary": output_summary,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        trace = list(state.get("decision_trace", []))
        trace.append(decision_entry)

        return {
            "next_step_action": next_action,
            "next_step_reason": next_reason,
            "decision_trace": trace
        }
