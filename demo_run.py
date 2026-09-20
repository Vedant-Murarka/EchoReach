"""
EchoReach Terminal Demo Script — Member 2 Task
Executes full 6-agent loop with guardrail checks, persona simulation, webhook trigger, and reasoning trace.
"""
import asyncio
import sys
from app.database import SessionLocal, Base, engine
from app.models import Lead, Touch, DecisionLog, SuppressionList
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
    print(" EchoReach — Personalized Multi-Touch Sales Outreach Agent Demo ")
    print(" Track D2 | Member 2 (Backend, State & Integrations Lead) ")
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
    print("STEP 2: Triggering Research Agent & Drafting Agent")
    print("--------------------------------------------------------------------------")
    facts = await AgentPipelineService.run_research_agent(db, lead)
    print(f"[+] Research Agent finished. Pulled {len(facts)} high-signal facts:")
    for f in facts:
        print(f"   * [{f.fact_type.upper()}] {f.content}")

    print("\nGenerating personalized touch draft + running Genericness Checker retry loop...")
    touch = AgentPipelineService.run_drafting_agent(db, lead, touch_number=1)
    print(f"[+] Touch #{touch.touch_number} Draft Created (Status: {touch.status})")
    print(f"Subject: {touch.subject}\n")
    print(f"Body:\n{touch.body}\n")

    print("\n--------------------------------------------------------------------------")
    print("STEP 3: Human Approval Queue & Guardrails Engine Check")
    print("--------------------------------------------------------------------------")
    success, msg = AgentPipelineService.process_human_approval(db, touch, action="approve")
    print(f"Guardrails & Sandbox Output: {msg}")
    print(f"Touch Final Status: {touch.status}")

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
    print("STEP 5: Reply Classifier Agent & Next-Step Decision Agent")
    print("--------------------------------------------------------------------------")
    pipeline_res = await AgentPipelineService.process_reply_and_next_step(
        db, lead, simulated_reply_text, persona_type="Eager Buyer"
    )
    print(f"[+] Classification Result: '{pipeline_res['classification']}' (Confidence: {pipeline_res['confidence']*100:.0f}%)")
    print(f"[+] Next-Step Action: {pipeline_res['next_step_action']}")
    print(f"Reasoning: {pipeline_res['reasoning']}")

    print("\n--------------------------------------------------------------------------")
    print("STEP 6: Printing Live Reasoning Trace / Decision Log Feed")
    print("--------------------------------------------------------------------------")
    logs = db.query(DecisionLog).filter(DecisionLog.lead_id == lead.id).order_by(DecisionLog.id.asc()).all()
    for idx, log in enumerate(logs, 1):
        print(f"[{idx}] Agent: {log.agent_name}")
        print(f"    Input:     {log.input_summary}")
        print(f"    Reasoning: {log.reasoning}")
        print(f"    Output:    {log.output_summary}\n")

    print("==========================================================================")
    print(" [SUCCESS] Full stateful lead sequence loop executed successfully!")
    print("==========================================================================")
    db.close()

if __name__ == "__main__":
    asyncio.run(run_terminal_demo())
