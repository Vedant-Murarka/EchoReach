import httpx
import logging
from app.config import settings

logger = logging.getLogger("echoreach.webhook")

class WebhookService:
    @staticmethod
    async def trigger_escalation_webhook(lead_name: str, company: str, classification: str, reply_text: str) -> bool:
        """
        Sends an instant real-time notification to Slack/Discord when a high-value reply or escalation occurs.
        """
        payload = {
            "text": f"🚨 *EchoReach High-Priority Lead Escalation* 🚨\n"
                    f"*Lead:* {lead_name} ({company})\n"
                    f"*Classification:* `{classification}`\n"
                    f"*Prospect Reply:* \"{reply_text[:200]}\"\n"
                    f"*Action Taken:* Escalated to Sales Rep Queue immediately."
        }

        success = False

        if settings.SLACK_WEBHOOK_URL:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(settings.SLACK_WEBHOOK_URL, json=payload)
                    if resp.status_code == 200:
                        logger.info("Successfully posted escalation notification to Slack webhook.")
                        success = True
            except Exception as e:
                logger.error(f"Failed to post to Slack webhook: {e}")

        if settings.DISCORD_WEBHOOK_URL:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(settings.DISCORD_WEBHOOK_URL, json={"content": payload["text"]})
                    if resp.status_code in [200, 204]:
                        logger.info("Successfully posted escalation notification to Discord webhook.")
                        success = True
            except Exception as e:
                logger.error(f"Failed to post to Discord webhook: {e}")

        if not settings.SLACK_WEBHOOK_URL and not settings.DISCORD_WEBHOOK_URL:
            logger.info(f"[SIMULATED WEBHOOK ALERT] Lead {lead_name} escalated! Webhook payload logged locally.")
            return True

        return success
