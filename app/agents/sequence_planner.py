import datetime
import logging
from typing import Dict, Any
from app.agents.state import LeadState

logger = logging.getLogger("echoreach.sequence_planner")

CADENCE_SCHEDULE = {
    1: {"day_offset": 0, "default_channel": "email", "intent": "Intro & Hook", "delay_desc": "Immediate send (Day 0)"},
    2: {"day_offset": 3, "default_channel": "linkedin", "intent": "Value & Pain Point", "delay_desc": "+3 Days from Touch 1"},
    3: {"day_offset": 7, "default_channel": "email", "intent": "Social Proof & Benchmark", "delay_desc": "+4 Days from Touch 2 (Day 7)"},
    4: {"day_offset": 12, "default_channel": "email", "intent": "Breakup Note", "delay_desc": "+5 Days from Touch 3 (Day 12)"}
}

class SequencePlannerAgent:
    """
    Node 4: Multi-Touch Sequence Planner (Cadence State Machine)
    Orchestrates touch progression across Day 0 -> 3 -> 7 -> 12 with multi-channel rotation (Email / LinkedIn).
    """

    @classmethod
    def run(cls, state: LeadState) -> Dict[str, Any]:
        current_touch = state.get("current_touch_number", 1)
        next_touch = current_touch
        
        # Check if current touch was completed/no-reply and needs advancement
        last_classification = state.get("reply_classification")
        if last_classification == "No Reply":
            if current_touch < 4:
                next_touch = current_touch + 1
            else:
                next_touch = 4

        cadence_info = CADENCE_SCHEDULE.get(next_touch, CADENCE_SCHEDULE[1])
        channel = cadence_info["default_channel"]
        intent = cadence_info["intent"]
        delay_desc = cadence_info["delay_desc"]

        input_summary = f"Sequence Cadence State Machine Evaluation (Current Touch: #{current_touch})"
        
        if next_touch <= 4:
            reasoning = f"Cadence Engine scheduled Touch #{next_touch} ({channel.upper()}) on cadence timing: '{delay_desc}'. Intent strategy: '{intent}'."
            output_summary = f"Active Stage: Cadence Touch #{next_touch} via {channel.upper()}"
        else:
            reasoning = "All 4 multi-touch cadence stages executed with zero prospect response. Sequence marked completed."
            output_summary = "STATUS: Sequence Completed"

        decision_entry = {
            "agent_name": "Sequence Planner Agent",
            "input_summary": input_summary,
            "reasoning": reasoning,
            "output_summary": output_summary,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        trace = list(state.get("decision_trace", []))
        trace.append(decision_entry)

        return {
            "current_touch_number": next_touch,
            "channel": channel,
            "decision_trace": trace
        }
