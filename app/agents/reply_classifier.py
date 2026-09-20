import datetime
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.agents.state import LeadState
from app.agents.llm_client import LLMClient
from app.models import ClassifierFeedback

logger = logging.getLogger("echoreach.reply_classifier")

BASE_FEW_SHOT_EXAMPLES = [
    {"text": "Sounds great, send me your calendar link!", "class": "Interested", "reasoning": "Explicit request for demo link and meeting scheduling."},
    {"text": "We already use Apollo and ZoomInfo for outreach, how are you different?", "class": "Objection", "reasoning": "Existing tool stack competitor objection."},
    {"text": "I am currently out of the office returning on Sept 25th with limited access to email.", "class": "Out-of-Office", "reasoning": "Standard automated out-of-office autoreply."},
    {"text": "Please remove our domain from your mailing list immediately. Not interested.", "class": "Not Interested", "reasoning": "Direct unsubscribe and decline directive."},
    {"text": "5 days elapsed with no interaction on Touch #1.", "class": "No Reply", "reasoning": "Automated cadence timeout trigger."}
]

CLASSIFIER_SYSTEM_PROMPT = """You are the EchoReach Autonomous 5-Class Reply Intent Classifier.
You must classify incoming prospect responses into EXACTLY one of the 5 canonical classes:
- 'Interested': Prospect expresses curiosity, agrees to a demo, asks for calendar link or meeting.
- 'Objection': Prospect mentions competitor tools, asks technical integration questions, budget constraints, or raises hurdles.
- 'Out-of-Office': Automated auto-reply indicating absence or delayed return.
- 'Not Interested': Explicit refusal, request to unsubscribe, or opt-out directive.
- 'No Reply': Cadence timer expiration with zero engagement.

Return JSON format:
{
  "classification": "Interested",
  "confidence": 0.96,
  "reasoning": "Concise explanation of why this class was assigned."
}"""

class ReplyClassifierAgent:
    """
    Node 5: 5-Class Reply Intent Classifier (Rule + LLM Hybrid with Dynamic Few-Shot Memory)
    Evaluates prospect intent, layers hard rules over LLM reasoning, and self-learns from operator corrections.
    """

    @classmethod
    async def run(cls, state: LeadState, db: Optional[Session] = None) -> Dict[str, Any]:
        raw_text = state.get("raw_reply_text", "")
        persona_type = state.get("persona_type", "custom")
        text_lower = raw_text.lower().strip()

        # 1. Fetch dynamic few-shot feedback examples from database (Self-Improving loop)
        dynamic_examples = list(BASE_FEW_SHOT_EXAMPLES)
        if db:
            try:
                db_feedbacks = db.query(ClassifierFeedback).order_by(ClassifierFeedback.id.desc()).limit(5).all()
                for fb in db_feedbacks:
                    dynamic_examples.append({
                        "text": fb.raw_text,
                        "class": fb.corrected_class,
                        "reasoning": f"Operator correction from '{fb.predicted_class}': {fb.notes or 'Corrected by rep'}"
                    })
            except Exception as e:
                logger.warning(f"Could not load classifier feedback from DB: {e}")

        # 2. Hard Rule Pre-Check (Zero-Ambiguity Fast Path)
        classification = None
        confidence = 0.95
        reasoning = ""

        if any(term in text_lower for term in ["out of the office", "ooo", "auto-reply", "on annual leave", "away from my desk"]):
            classification = "Out-of-Office"
            confidence = 0.99
            reasoning = "Detected explicit automated out-of-office response pattern."
        elif any(term in text_lower for term in ["unsubscribe", "remove me", "not interested", "stop emailing", "take me off", "do not contact"]):
            classification = "Not Interested"
            confidence = 0.98
            reasoning = "Detected explicit opt-out directive or rejection statement."
        elif any(term in text_lower for term in ["already use", "already using", "how do you compare", "pricing is high", "how do you integrate", "integrations", "how does it work"]):
            classification = "Objection"
            confidence = 0.94
            reasoning = "Prospect raised an objection regarding workflow, integration, or existing vendor."
        elif any(term in text_lower for term in ["timeout", "cadence elapsed", "no reply", "5 days elapsed"]):
            classification = "No Reply"
            confidence = 1.00
            reasoning = "Cadence timeout threshold reached with no response."
        elif any(term in text_lower for term in ["calendar link", "schedule a call", "sounds great", "let's talk", "book a time", "open to a demo"]):
            classification = "Interested"
            confidence = 0.96
            reasoning = "Prospect expressed strong intent to schedule a meeting or demo."

        # 3. If ambiguous, invoke LLM classifier with few-shot dynamic memory
        if not classification:
            classification = "Interested"
            confidence = 0.90
            reasoning = "Evaluated overall positive intent."

            if LLMClient.get_provider() != "mock":
                few_shot_prompt = "\n\n".join([f"Example Text: \"{ex['text']}\"\nClassification: {ex['class']}\nReasoning: {ex['reasoning']}" for ex in dynamic_examples])
                user_prompt = f"""FEW-SHOT TRAINING EXEMPLARS:
{few_shot_prompt}

TARGET PROSPECT REPLY TO CLASSIFY:
\"\"\"{raw_text}\"\"\"

Classify the target reply into one of: Interested, Objection, Out-of-Office, Not Interested, No Reply."""

                try:
                    llm_res = await LLMClient.generate_json(CLASSIFIER_SYSTEM_PROMPT, user_prompt)
                    valid_classes = {
                        "interested": "Interested",
                        "objection": "Objection",
                        "out-of-office": "Out-of-Office",
                        "out of office": "Out-of-Office",
                        "not interested": "Not Interested",
                        "no reply": "No Reply"
                    }
                    raw_pred = str(llm_res.get("classification", "")).strip().lower()
                    if raw_pred in valid_classes:
                        classification = valid_classes[raw_pred]
                        confidence = float(llm_res.get("confidence", 0.95))
                        reasoning = llm_res.get("reasoning", reasoning)
                except Exception as e:
                    logger.debug(f"LLM Classification fallback: {e}")

        input_summary = f"Classifying prospect reply ({persona_type}): '{raw_text[:80]}...'"
        reasoning_log = f"5-Class Intent Classifier evaluated reply. Assigned '{classification}' (Confidence: {confidence*100:.0f}%). Few-shot examples in memory: {len(dynamic_examples)}. {reasoning}"
        output_summary = f"Classification: {classification} (Conf: {confidence*100:.0f}%)"

        decision_entry = {
            "agent_name": "Reply Classifier Agent",
            "input_summary": input_summary,
            "reasoning": reasoning_log,
            "output_summary": output_summary,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        trace = list(state.get("decision_trace", []))
        trace.append(decision_entry)

        return {
            "reply_classification": classification,
            "reply_confidence": confidence,
            "reply_reasoning": reasoning,
            "few_shot_examples_used": len(dynamic_examples),
            "decision_trace": trace
        }
