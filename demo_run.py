"""
EchoReach Terminal Demo Script — Member 1 & 2 Execution
Executes full LangGraph 6-agent state machine with Genericness Checker retry loop, guardrail checks, persona simulation, webhook trigger, and live reasoning trace.
"""
import asyncio
import sys
from app.database import SessionLocal, Base, engine
from app.models import Lead, Touch, DecisionLog, SuppressionList, ClassifierFeedback
from app.services.agent_pipeline import AgentPipelineService
from seed_data import seed_database

# Fix Windows console encoding if needed
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def run_terminal_demo():
    print("==========================================================================")
    print(" EchoReach — Autonomous Multi-Touch Sales Outreach Agent (LangGraph) ")
    print(" Track D2 | Full 6-Agent State Machine & Guardrail Execution ")
    print("==========================================================================\n")

    # Ensure database is seeded
    seed_database()
    db = SessionLocal()

    print("\n--------------------------------------------------------------------------")
    print("STEP 1: Fetching target lead from database pipeline")
    print("--------------------------------------------------------------------------")
    lead = db.query(Lead).filter(Lead.company == "Apex Dynamics").first()
    print(f"Target Prospect: {lead.name} | {lead.title} @ {lead.company}")
    print(f"Email: {lead.email} | Stage: {lead.stage}")

    print("\n--------------------------------------------------------------------------")
    print("STEP 2: Triggering LangGraph Pipeline (Research -> Drafting -> Genericness Checker)")
    print("--------------------------------------------------------------------------")
    facts, touch = await AgentPipelineService.run_research_and_draft_graph(db, lead, touch_number=1)
    print(f"[+] Research Agent finished. Pulled {len(facts)} high-signal facts:")
    for f in facts:
        print(f"   * [{f.fact_type.upper()}] {f.content}")

    print(f"\n[+] Drafting & Genericness Checker Graph completed (Touch ID: {touch.id}, Status: {touch.status})")
    print(f"Subject: {touch.subject}\n")
    print(f"Body:\n{touch.body}\n")

    print("\n--------------------------------------------------------------------------")
    print("STEP 3: Human Approval Queue & Guardrails Engine Check")
    print("--------------------------------------------------------------------------")
    success, msg = AgentPipelineService.process_human_approval(db, touch, action="approve")
    print(f"Guardrails & Sandbox Output: {msg}")
    print(f"Touch Final Status: {touch.status} | Lead Stage: {lead.stage}")

    print("\n--------------------------------------------------------------------------")
    print("STEP 4: Prospect Persona Reply Simulator")
    print("--------------------------------------------------------------------------")
    simulated_reply_text = (
        f"Hi! Thanks for reaching out. Your note on our Series B funding and hiring plans was spot on. "
        f"We're looking to automate our outreach ops right now. Could we schedule a 15-min call this Thursday?"
    )
    print(f"Simulating Prospect Persona Reply ('Eager Buyer'):")
    print(f"\"{simulated_reply_text}\"\n")

    print("--------------------------------------------------------------------------")
    print("STEP 5: Reply Classifier Agent (with Self-Improving Memory) & Next-Step Agent")
    print("--------------------------------------------------------------------------")
    pipeline_res = await AgentPipelineService.process_reply_and_next_step(
        db, lead, simulated_reply_text, persona_type="Eager Buyer"
    )
    print(f"[+] Classification Result: '{pipeline_res['classification']}' (Confidence: {pipeline_res['confidence']*100:.0f}%)")
    print(f"[+] Next-Step Action: {pipeline_res['next_step_action']}")
    print(f"Reasoning: {pipeline_res['reasoning']}")

    print("\n--------------------------------------------------------------------------")
    print("STEP 6: Printing Live Reasoning Trace / Decision Log Feed (Explainability)")
    print("--------------------------------------------------------------------------")
    logs = db.query(DecisionLog).filter(DecisionLog.lead_id == lead.id).order_by(DecisionLog.id.asc()).all()
    for idx, log in enumerate(logs, 1):
        print(f"[{idx}] Agent: {log.agent_name}")
        print(f"    Input:     {log.input_summary}")
        print(f"    Reasoning: {log.reasoning}")
        print(f"    Output:    {log.output_summary}\n")

    print("==========================================================================")
    print(" [SUCCESS] Full stateful LangGraph lead sequence loop executed successfully!")
    print("==========================================================================")
    db.close()

if __name__ == "__main__":
    asyncio.run(run_terminal_demo())
