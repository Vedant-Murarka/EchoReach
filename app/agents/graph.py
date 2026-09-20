import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from app.agents.state import LeadState
from app.agents.research_agent import ResearchAgent
from app.agents.drafting_agent import DraftingAgent
from app.agents.genericness_checker import GenericnessCheckerAgent
from app.agents.sequence_planner import SequencePlannerAgent
from app.agents.reply_classifier import ReplyClassifierAgent
from app.agents.next_step_agent import NextStepDecisionAgent

logger = logging.getLogger("echoreach.graph")

def should_retry_draft(state: LeadState) -> Literal["drafting", "__end__"]:
    """
    Conditional Routing Edge:
    If genericness check failed and attempts < 2, loop back to Drafting Agent with feedback.
    Otherwise, proceed to Human Approval Queue (END).
    """
    passed = state.get("genericness_passed", False)
    retries = state.get("retry_count", 0)

    if not passed and retries < 2:
        logger.info(f"Genericness check failed. Retrying draft (Attempt #{retries})...")
        return "drafting"
    
    return "__end__"

def build_outreach_generation_graph():
    """
    Builds the LangGraph state machine for Research -> Drafting -> Genericness Check (Retry Loop).
    """
    builder = StateGraph(LeadState)

    # Add Nodes
    builder.add_node("research", ResearchAgent.run)
    builder.add_node("drafting", DraftingAgent.run)
    builder.add_node("genericness_check", GenericnessCheckerAgent.run)

    # Add Edges
    builder.set_entry_point("research")
    builder.add_edge("research", "drafting")
    builder.add_edge("drafting", "genericness_check")
    
    # Conditional retry edge
    builder.add_conditional_edges(
        "genericness_check",
        should_retry_draft,
        {
            "drafting": "drafting",
            "__end__": END
        }
    )

    return builder.compile()

def build_reply_handling_graph():
    """
    Builds the LangGraph state machine for Reply Classification -> Next-Step Decision.
    """
    builder = StateGraph(LeadState)

    builder.add_node("reply_classifier", ReplyClassifierAgent.run)
    builder.add_node("next_step", NextStepDecisionAgent.run)

    builder.set_entry_point("reply_classifier")
    builder.add_edge("reply_classifier", "next_step")
    builder.add_edge("next_step", END)

    return builder.compile()

# Pre-compiled graph singletons
outreach_graph = build_outreach_generation_graph()
reply_graph = build_reply_handling_graph()

class EchoReachGraphService:
    """
    Orchestration interface for executing stateful multi-agent graphs.
    """

    @classmethod
    async def run_generation_pipeline(cls, initial_state: LeadState) -> LeadState:
        """Executes Research -> Drafting -> Genericness Check Loop"""
        final_state = await outreach_graph.ainvoke(initial_state)
        return final_state

    @classmethod
    async def run_reply_pipeline(cls, initial_state: LeadState, db_session = None) -> LeadState:
        """Executes Reply Classifier -> Next-Step Decision"""
        # Node execution with DB access for dynamic few-shot learning
        state_after_classifier = await ReplyClassifierAgent.run(initial_state, db=db_session)
        merged_state = {**initial_state, **state_after_classifier}
        state_after_next_step = await NextStepDecisionAgent.run(merged_state)
        final_state = {**merged_state, **state_after_next_step}
        return final_state
