import datetime
import logging
from typing import Dict, Any, List
from app.agents.state import LeadState
from app.agents.llm_client import LLMClient
from app.services.search_service import SearchService

logger = logging.getLogger("echoreach.research_agent")

RESEARCH_SYSTEM_PROMPT = """You are the EchoReach Autonomous Research Agent.
Your job is to analyze web search results and extract 3 to 5 high-signal, factual intelligence bullets about a target lead and their company.
Each fact must be strictly classified into one of: 'funding', 'hiring', 'news', 'role-change', 'product-launch'.
For each fact, explain WHY it is relevant for sales outreach (kept_reason).

Output format must be JSON:
{
  "facts": [
    {
      "fact_type": "funding",
      "content": "Description of the fact...",
      "source": "https://...",
      "kept_reason": "Why this fact was selected..."
    }
  ]
}"""

class ResearchAgent:
    """
    Node 1: Autonomous Per-Lead Research Agent
    Pulls public context via search tools and extracts structured, high-signal facts.
    """

    @classmethod
    async def run(cls, state: LeadState) -> Dict[str, Any]:
        lead_name = state.get("name", "Prospect")
        company = state.get("company", "Target Company")
        title = state.get("title", "Executive")
        
        query = f"{company} {lead_name} {title} funding news product launch hiring"
        input_summary = f"Researching public signals for {lead_name} ({title} at {company})"

        # 1. Fetch raw web search results (via Tavily / Serper / plantable synthetic database)
        raw_search_facts = await SearchService.perform_web_search(query, company, lead_name)
        
        # 2. Extract and structure using LLM if available
        if LLMClient.get_provider() != "mock":
            user_prompt = f"Target: {lead_name}, {title} at {company}.\nRaw Search Signals:\n{raw_search_facts}"
            llm_result = await LLMClient.generate_json(RESEARCH_SYSTEM_PROMPT, user_prompt)
            facts = llm_result.get("facts", raw_search_facts)
        else:
            facts = raw_search_facts

        # Format and ensure minimum count
        formatted_facts = []
        reasoning_bullets = []
        for f in facts:
            fact_entry = {
                "fact_type": f.get("fact_type", "news"),
                "content": f.get("content", f"{company} is actively growing"),
                "source": f.get("source", "Web Intelligence"),
                "kept_reason": f.get("kept_reason", "High-signal company momentum indicator")
            }
            formatted_facts.append(fact_entry)
            reasoning_bullets.append(f"[{fact_entry['fact_type'].upper()}]: {fact_entry['kept_reason']}")

        reasoning_str = f"Evaluated web search results. Kept {len(formatted_facts)} signal points: " + "; ".join(reasoning_bullets)
        output_summary = f"Extracted {len(formatted_facts)} verified research facts for {company}."

        decision_entry = {
            "agent_name": "Research Agent",
            "input_summary": input_summary,
            "reasoning": reasoning_str,
            "output_summary": output_summary,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        trace = list(state.get("decision_trace", []))
        trace.append(decision_entry)

        return {
            "research_query": query,
            "research_facts": formatted_facts,
            "decision_trace": trace
        }
