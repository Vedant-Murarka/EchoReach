import datetime
import logging
from typing import Dict, Any, List
from app.agents.state import LeadState
from app.agents.llm_client import LLMClient

logger = logging.getLogger("echoreach.drafting_agent")

DRAFTING_SYSTEM_PROMPT = """You are the EchoReach Personalized Drafting Agent.
Your job is to generate high-converting, personalized B2B outreach messages (email or LinkedIn DM).

RULES:
1. You MUST explicitly reference at least 2 concrete research facts provided in the prompt inline.
2. NO generic filler phrases (NEVER say "hope this email finds you well", "reach out to touch base", "synergy", "quick question", etc.).
3. Match the specific touch number and intent:
   - Touch 1 (Day 0, Intro): Custom hook, reference recent news/funding, soft conversational CTA.
   - Touch 2 (Day 3, Value): Tie research fact to operational pain points & automation benefits.
   - Touch 3 (Day 7, Social Proof): Case study & benchmark metrics relevant to their sector.
   - Touch 4 (Day 12, Breakup): Professional close, respectful final check-in, leaves door open.
4. If rewrite feedback is provided, strictly follow it to fix past genericness issues.

Return JSON format:
{
  "subject": "Subject line here",
  "body": "Body text here (multi-paragraph with proper linebreaks)"
}"""

class DraftingAgent:
    """
    Node 2: Personalized Multi-Touch Drafting Agent
    Synthesizes research facts into hyper-targeted outreach drafts tailored by touch intent.
    """

    TOUCH_INTENTS = {
        1: ("Intro & Custom Hook", "Introduce value proposition hooked to latest company milestone with a soft CTA."),
        2: ("Value & Pain Point", "Connect recent hiring or growth initiatives to workflow optimization bottlenecks."),
        3: ("Social Proof & Case Study", "Share industry case study showing 3x conversion lift from autonomous personalization."),
        4: ("Breakup Touch", "Respectful final note closing the active sequence while leaving the relationship open.")
    }

    @classmethod
    async def run(cls, state: LeadState) -> Dict[str, Any]:
        lead_name = state.get("name", "Prospect")
        company = state.get("company", "Company")
        title = state.get("title", "Executive")
        touch_number = state.get("current_touch_number", 1)
        channel = state.get("channel", "email")
        facts = state.get("research_facts", [])
        feedback = state.get("genericness_feedback", "")
        retry_count = state.get("retry_count", 0)

        intent_title, intent_desc = cls.TOUCH_INTENTS.get(touch_number, cls.TOUCH_INTENTS[1])
        
        # Prepare facts text
        facts_text = "\n".join([f"- [{f.get('fact_type', 'news').upper()}]: {f.get('content', '')}" for f in facts])
        if not facts_text:
            facts_text = f"- [NEWS]: {company} announced aggressive team expansion and technical scaling."

        user_prompt = f"""Target Lead: {lead_name}, {title} at {company}
Channel: {channel.upper()}
Touch Number: #{touch_number} ({intent_title})
Touch Intent: {intent_desc}

Verified Research Facts:
{facts_text}

Previous Reviewer Feedback (if any):
{feedback if feedback else "None. First generation pass."}

Draft a compelling, natural outreach message that quotes/incorporates at least 2 research facts."""

        # Call LLM
        subject = f"Personalized touch for {company} — {intent_title}"
        body = ""

        if LLMClient.get_provider() != "mock":
            llm_result = await LLMClient.generate_json(DRAFTING_SYSTEM_PROMPT, user_prompt)
            subject = llm_result.get("subject", subject)
            body = llm_result.get("body", "")

        # Heuristic fallback if LLM is mock or empty
        if not body:
            f1 = facts[0]["content"] if len(facts) > 0 else f"{company} is scaling operations"
            f2 = facts[1]["content"] if len(facts) > 1 else f"{company} is actively hiring top talent"
            
            if touch_number == 1:
                body = f"Hi {lead_name},\n\nI noticed that {f1}. Also, seeing that {f2}, scaling outreach without losing quality is essential.\n\nEchoReach enables autonomous multi-touch sequences with verifiable guardrails. Would you be open to a 10-minute chat this week?"
            elif touch_number == 2:
                body = f"Hi {lead_name},\n\nFollowing up on my previous note. Given that {f1}, streamlining SDR workflows becomes a major competitive edge.\n\nWould you like a 5-minute walkthrough of our automated personalization engine?"
            elif touch_number == 3:
                body = f"Hi {lead_name},\n\nTeams experiencing growth similar to {f2} achieved a 3.4x lift in meeting conversion with our stateful outreach agent.\n\nI'd be happy to share the case study if you're interested."
            else:
                body = f"Hi {lead_name},\n\nI understand you're busy scaling initiatives around {f1}. I won't continue following up, but feel free to reach out if automated outreach becomes a priority later on."

        input_summary = f"Generating Touch #{touch_number} ({channel}) for {lead_name} at {company}"
        reasoning = f"Selected Touch #{touch_number} intent: '{intent_title}'. Injected {min(len(facts), 2)} research facts. Tailored for {channel} channel."
        if feedback:
            reasoning += f" Applied revision feedback: '{feedback}' (Retry #{retry_count})."

        output_summary = f"Drafted subject: '{subject}' (Length: {len(body)} chars)."

        decision_entry = {
            "agent_name": "Drafting Agent",
            "input_summary": input_summary,
            "reasoning": reasoning,
            "output_summary": output_summary,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        trace = list(state.get("decision_trace", []))
        trace.append(decision_entry)

        return {
            "draft_subject": subject,
            "draft_body": body,
            "decision_trace": trace
        }
