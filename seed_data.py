"""
EchoReach Dataset Seeder Script — Member 2 Task
Seeds database (SQLite / Supabase PostgreSQL) with 15 synthetic leads, plantable research facts, suppression rules, and classifier feedback exemplars.
"""
from app.database import SessionLocal, engine, Base
from app.models import Lead, ResearchFact, SuppressionList, DailySendCounter, ClassifierFeedback, Reply, Touch, DecisionLog

SYNTHETIC_LEADS = [
    {
        "name": "Sarah Jenkins",
        "title": "VP of Revenue Operations",
        "company": "Apex Dynamics",
        "email": "sarah.jenkins@apexdynamics.io",
        "linkedin_url": "https://linkedin.com/in/sarahjenkins-apex",
        "stage": "New",
        "facts": [
            {"type": "funding", "content": "Apex Dynamics raised $18M Series B led by Sequoia Capital.", "source": "https://techcrunch.com/apex-series-b"},
            {"type": "hiring", "content": "Apex Dynamics is scaling sales ops with 12 open positions.", "source": "https://linkedin.com/jobs/apex"}
        ]
    },
    {
        "name": "Michael Chen",
        "title": "Head of Growth Marketing",
        "company": "PulseMetrics",
        "email": "mchen@pulsemetrics.co",
        "linkedin_url": "https://linkedin.com/in/mchen-growth",
        "stage": "New",
        "facts": [
            {"type": "product-launch", "content": "PulseMetrics launched Real-Time Customer Analytics v3.", "source": "https://producthunt.com/pulsemetrics-v3"},
            {"type": "news", "content": "Michael Chen spoke at SaaStr Annual on AI-assisted pipeline growth.", "source": "https://saastr.com/speakers/mchen"}
        ]
    },
    {
        "name": "Elena Rostova",
        "title": "Director of Sales Development",
        "company": "CloudForge AI",
        "email": "elena@cloudforge.ai",
        "linkedin_url": "https://linkedin.com/in/elena-rostova",
        "stage": "New",
        "facts": [
            {"type": "funding", "content": "CloudForge AI secured $8M seed round to build automated sales workflows.", "source": "https://venturebeat.com/cloudforge-seed"},
            {"type": "role-change", "content": "Elena was recently promoted to Director of Sales Development.", "source": "https://linkedin.com/in/elena-rostova"}
        ]
    },
    {
        "name": "David Miller",
        "title": "Chief Commercial Officer",
        "company": "Nexus Logistics",
        "email": "dmiller@nexuslogistics.com",
        "linkedin_url": "https://linkedin.com/in/david-miller-nexus",
        "stage": "New",
        "facts": [
            {"type": "news", "content": "Nexus Logistics expanded into European markets with 3 new hubs.", "source": "https://freightwaves.com/nexus-expansion"},
            {"type": "hiring", "content": "Nexus Logistics posted open roles for enterprise BDR team leads.", "source": "https://nexuslogistics.com/careers"}
        ]
    },
    {
        "name": "Priya Sharma",
        "title": "VP of Enterprise Sales",
        "company": "DataSphere Technologies",
        "email": "priya.sharma@datasphere.net",
        "linkedin_url": "https://linkedin.com/in/priyasharma-sales",
        "stage": "New",
        "facts": [
            {"type": "product-launch", "content": "DataSphere launched AI Data Cleanroom for enterprise compliance.", "source": "https://businesswire.com/datasphere-cleanroom"},
            {"type": "funding", "content": "DataSphere reached $40M ARR landmark in Q2.", "source": "https://techcrunch.com/datasphere-arr"}
        ]
    },
    {
        "name": "Marcus Vance",
        "title": "Co-Founder & CEO",
        "company": "Vectra Health",
        "email": "marcus@vectrahealth.org",
        "linkedin_url": "https://linkedin.com/in/marcusvance",
        "stage": "New",
        "facts": [
            {"type": "news", "content": "Vectra Health partnered with Mayo Clinic for digital patient intake.", "source": "https://digitalhealth.com/vectra-mayo"},
            {"type": "hiring", "content": "Vectra Health is hiring senior healthcare account executives.", "source": "https://vectrahealth.org/jobs"}
        ]
    },
    {
        "name": "Jessica Taylor",
        "title": "Head of Business Development",
        "company": "FinFlow Pay",
        "email": "jtaylor@finflow.io",
        "linkedin_url": "https://linkedin.com/in/jtaylor-finflow",
        "stage": "New",
        "facts": [
            {"type": "funding", "content": "FinFlow Pay closed $25M Series B for cross-border payment rails.", "source": "https://fintechfutures.com/finflow-series-b"},
            {"type": "product-launch", "content": "FinFlow Pay launched instant payouts API for B2B platforms.", "source": "https://finflow.io/blog/instant-payouts"}
        ]
    },
    {
        "name": "Alexandre Dubois",
        "title": "VP of Global Demand Gen",
        "company": "Synthetix AI",
        "email": "alex.dubois@synthetix.ai",
        "linkedin_url": "https://linkedin.com/in/alex-dubois-ai",
        "stage": "New",
        "facts": [
            {"type": "news", "content": "Synthetix AI won Best Enterprise AI Tool at TechX 2026.", "source": "https://techx.com/winners/synthetix"},
            {"type": "hiring", "content": "Synthetix AI expanding North American sales headcount by 50%.", "source": "https://synthetix.ai/careers"}
        ]
    },
    {
        "name": "Rachel Adams",
        "title": "Director of Revenue Operations",
        "company": "OmniStack",
        "email": "rachel@omnistack.com",
        "linkedin_url": "https://linkedin.com/in/rachel-adams-omni",
        "stage": "New",
        "facts": [
            {"type": "product-launch", "content": "OmniStack launched unified CRM data sync extension.", "source": "https://producthunt.com/omnistack-sync"},
            {"type": "role-change", "content": "Rachel Adams stepped into RevOps leadership role in Q1.", "source": "https://linkedin.com/in/rachel-adams-omni"}
        ]
    },
    {
        "name": "Kevin O'Connor",
        "title": "VP of Sales",
        "company": "CyberShield Defense",
        "email": "koconnor@cybershield.sec",
        "linkedin_url": "https://linkedin.com/in/koconnor-sec",
        "stage": "New",
        "facts": [
            {"type": "funding", "content": "CyberShield secured $30M growth round from Horizon Ventures.", "source": "https://darkreading.com/cybershield-30m"},
            {"type": "news", "content": "CyberShield published Annual Ransomware Preparedness Index.", "source": "https://cybershield.sec/report-2026"}
        ]
    },
    {
        "name": "Anita Roy",
        "title": "Head of Strategic Partnerships",
        "company": "Zenith Cloud",
        "email": "anita.roy@zenithcloud.io",
        "linkedin_url": "https://linkedin.com/in/anitaroy-cloud",
        "stage": "New",
        "facts": [
            {"type": "news", "content": "Zenith Cloud announced strategic partnership with AWS.", "source": "https://aws.amazon.com/partners/zenith"},
            {"type": "hiring", "content": "Zenith Cloud is hiring partner account managers across EMEA.", "source": "https://zenithcloud.io/jobs"}
        ]
    },
    {
        "name": "Tom Bradley",
        "title": "Chief Revenue Officer",
        "company": "HyperDrive CRM",
        "email": "tbradley@hyperdrivecrm.com",
        "linkedin_url": "https://linkedin.com/in/tombradley-cro",
        "stage": "New",
        "facts": [
            {"type": "product-launch", "content": "HyperDrive CRM released AI Co-pilot for Deal Intelligence.", "source": "https://techcrunch.com/hyperdrive-copilot"},
            {"type": "funding", "content": "HyperDrive crossed $50M ARR benchmark.", "source": "https://saastr.com/hyperdrive-milestone"}
        ]
    },
    {
        "name": "Opt-Out Test Lead",
        "title": "Marketing Manager",
        "company": "Suppressed Corp",
        "email": "do-not-contact@suppressedcorp.com",
        "linkedin_url": "https://linkedin.com/in/test-suppressed",
        "stage": "New",
        "facts": [
            {"type": "news", "content": "Company updated privacy & opt-out policy.", "source": "https://suppressedcorp.com/privacy"}
        ]
    },
    {
        "name": "Domain Blocked Lead",
        "title": "Sales Lead",
        "company": "Blacklisted Org",
        "email": "john@blacklisted-domain.com",
        "linkedin_url": "https://linkedin.com/in/john-blacklisted",
        "stage": "New",
        "facts": [
            {"type": "news", "content": "Domain added to global suppression list for testing.", "source": "https://example.com/test"}
        ]
    },
    {
        "name": "Demo Lead One",
        "title": "VP of Sales Operations",
        "company": "Acme Software",
        "email": "demo.lead@acmesoftware.com",
        "linkedin_url": "https://linkedin.com/in/demolead-acme",
        "stage": "New",
        "facts": [
            {"type": "funding", "content": "Acme Software raised $12M Series A funding.", "source": "https://techcrunch.com/acme-12m"},
            {"type": "hiring", "content": "Acme Software is hiring 10 SDRs this quarter.", "source": "https://acmesoftware.com/careers"}
        ]
    }
]

def seed_database():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()

    # Clear existing data for clean re-seeding
    db.query(ClassifierFeedback).delete()
    db.query(Reply).delete()
    db.query(DecisionLog).delete()
    db.query(ResearchFact).delete()
    db.query(Touch).delete()
    db.query(Lead).delete()
    db.query(SuppressionList).delete()
    db.query(DailySendCounter).delete()
    db.commit()

    print(f"Seeding {len(SYNTHETIC_LEADS)} synthetic leads...")

    for lead_data in SYNTHETIC_LEADS:
        lead = Lead(
            name=lead_data["name"],
            title=lead_data["title"],
            company=lead_data["company"],
            email=lead_data["email"],
            linkedin_url=lead_data["linkedin_url"],
            stage=lead_data["stage"],
            current_touch_number=1,
            status="Active"
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        for fact in lead_data.get("facts", []):
            rf = ResearchFact(
                lead_id=lead.id,
                fact_type=fact["type"],
                content=fact["content"],
                source=fact["source"],
                kept_reason="Extracted high-signal company momentum indicator"
            )
            db.add(rf)
        db.commit()

    # Seed suppression entries for guardrail verification
    db.add(SuppressionList(email="do-not-contact@suppressedcorp.com", reason="Explicit user opt-out request"))
    db.add(SuppressionList(domain="blacklisted-domain.com", reason="Domain-wide opt-out policy"))

    # Seed initial classifier feedback exemplars (Self-Improving Classifier Memory)
    db.add(ClassifierFeedback(
        raw_text="We already have a dedicated tool for this, but could you send over a 1-pager comparing your security model?",
        predicted_class="Interested",
        corrected_class="Objection",
        notes="Prospect has competitor tool but requested security spec - classify as Objection"
    ))
    db.add(ClassifierFeedback(
        raw_text="I will be away from office until October 2nd. For urgent matters contact team@domain.com",
        predicted_class="Interested",
        corrected_class="Out-of-Office",
        notes="Standard out-of-office message format"
    ))
    db.commit()

    print("Database seeding completed successfully!")
    print(f"Total Leads Created: {db.query(Lead).count()}")
    print(f"Total Research Facts Created: {db.query(ResearchFact).count()}")
    print(f"Total Suppression Entries: {db.query(SuppressionList).count()}")
    print(f"Total Classifier Feedback Exemplars: {db.query(ClassifierFeedback).count()}")
    db.close()

if __name__ == "__main__":
    seed_database()
