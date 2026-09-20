import random
from typing import Dict, Any

class ProspectSimulatorService:
    PERSONAS = {
        "eager_buyer": {
            "name": "Eager Buyer (Interested)",
            "text": "Thanks for reaching out! Your point about scaling our team and automating onboarding resonated with me. Could we set up a 15-minute call this Thursday at 2 PM EST to discuss pricing and demo details?",
            "expected_classification": "Interested"
        },
        "skeptic": {
            "name": "Skeptic (Objection)",
            "text": "This sounds interesting, but we already use a legacy CRM tool for our sequences. How does your platform integrate with existing tech stacks without creating data silos?",
            "expected_classification": "Objection"
        },
        "out_of_office": {
            "name": "Out-of-Office (OOO Auto-Reply)",
            "text": "Hello, I am out of the office attending the AI Summit until next Tuesday, October 15th, with limited access to email. For urgent inquiries, please contact sales-ops@company.com.",
            "expected_classification": "Out-of-Office"
        },
        "hard_no": {
            "name": "Hard No (Not Interested)",
            "text": "Please remove me from your mailing list. We are not interested in buying new tools this quarter.",
            "expected_classification": "Not Interested"
        },
        "ghost": {
            "name": "Ghost / No Reply (Timeout)",
            "text": "[System Cadence Timeout: 5 Days elapsed with zero recipient activity]",
            "expected_classification": "No Reply"
        }
    }

    @classmethod
    def generate_simulated_reply(cls, persona_type: str, lead_name: str, company: str) -> Dict[str, Any]:
        persona_key = persona_type.lower().replace(" ", "_")
        persona_data = cls.PERSONAS.get(persona_key, cls.PERSONAS["eager_buyer"])
        
        reply_text = persona_data["text"].format(lead_name=lead_name, company=company)
        
        return {
            "persona_type": persona_data["name"],
            "raw_text": reply_text,
            "expected_classification": persona_data["expected_classification"],
            "confidence": round(random.uniform(0.92, 0.99), 2)
        }
