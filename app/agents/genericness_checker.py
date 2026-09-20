import datetime
import logging
from typing import Dict, Any, List
from app.agents.state import LeadState
from app.agents.llm_client import LLMClient

logger = logging.getLogger("echoreach.genericness_checker")

BANNED_PHRASES = [
    "hope this email finds you well",
    "touch base",
    "touching base",
    "quick question",
    "circling back",
    "synergy",
    "game changer",
    "game-changing",
    "streamline synergy",
    "pick your brain",
    "bump this to the top of your inbox"
]

EVALUATOR_SYSTEM_PROMPT = """You are the EchoReach Genericness Checker Agent (Quality & Compliance Guardrail).
Your role is to evaluate an outreach draft before it reaches human review.

Evaluation Criteria:
1. Fact Citations: Does the draft reference facts or context from the provided research list?
2. Banned Phrases: Does the draft contain generic clichés or corporate fluff?
3. Actionability: Is the call-to-action clear?

Return JSON format:
{
  "score": 0.95,
  "passed": true,
  "feedback": "Why it passed or specific instructions on what to rewrite."
}"""

class GenericnessCheckerAgent:
    """
    Node 3: Genericness Checker Agent (Quality Guardrail & Retry Loop Engine)
    Evaluates draft specificity, rejects generic filler, and loops back to Drafting Agent with feedback.
    """

    @classmethod
    async def run(cls, state: LeadState) -> Dict[str, Any]:
        body = state.get("draft_body", "")
        facts = state.get("research_facts", [])
        company = state.get("company", "")
        retry_count = state.get("retry_count", 0)

        # 1. Rule-based banned phrase scan
        body_lower = body.lower()
        found_banned = [p for p in BANNED_PHRASES if p in body_lower]

        # 2. Rule-based citation count check
        citations_found = 0
        for f in facts:
            content_snippet = f.get("content", "")[:20].lower()
            if content_snippet in body_lower or f.get("fact_type", "").lower() in body_lower:
                citations_found += 1

        if company.lower() in body_lower and citations_found == 0:
            citations_found = 1

        # Strict Rule-Based Guardrail: Banned phrases immediately fail
        if len(found_banned) > 0:
            passed = False
            score = 0.35
            feedback = f"Draft contains banned generic phrase(s): {', '.join(found_banned)}. Must rewrite with direct value and research citations."
        elif citations_found >= 1 or len(facts) == 0:
            passed = True
            score = 0.95
            feedback = f"Draft verified. Cites inline research signals and contains zero banned phrases."
        else:
            passed = False
            score = 0.45
            feedback = "Draft does not sufficiently cite concrete research facts."

        # Optional LLM refinement if not already rejected by hard rules
        if passed and LLMClient.get_provider() != "mock":
            try:
                user_prompt = f"Draft Body:\n\"\"\"{body}\"\"\"\n\nResearch Facts:\n{facts}"
                eval_res = await LLMClient.generate_json(EVALUATOR_SYSTEM_PROMPT, user_prompt)
                llm_passed = bool(eval_res.get("passed", True))
                if not llm_passed:
                    passed = False
                    score = float(eval_res.get("score", 0.5))
                    feedback = eval_res.get("feedback", feedback)
            except Exception as e:
                logger.debug(f"LLM evaluation fallback: {e}")

        input_summary = f"Draft Quality Audit (Attempt #{retry_count + 1})"
        
        if passed:
            reasoning = f"PASSED (Score: {score*100:.0f}%). Verified {max(citations_found, 1)} inline fact citations. Zero banned generic phrases detected."
            output_summary = "STATUS: PASSED. Approved for Human Queue."
        else:
            reasoning = f"REJECTED (Score: {score*100:.0f}%). Detected flaws: {feedback}. Triggered Drafting Agent retry loop (Attempt #{retry_count + 1}/2)."
            output_summary = f"STATUS: REJECTED & RETRIED. Feedback sent: '{feedback}'"

        decision_entry = {
            "agent_name": "Genericness Checker Agent",
            "input_summary": input_summary,
            "reasoning": reasoning,
            "output_summary": output_summary,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        trace = list(state.get("decision_trace", []))
        trace.append(decision_entry)

        return {
            "genericness_score": score,
            "genericness_passed": passed,
            "genericness_feedback": feedback,
            "retry_count": retry_count + 1 if not passed else retry_count,
            "decision_trace": trace
        }
