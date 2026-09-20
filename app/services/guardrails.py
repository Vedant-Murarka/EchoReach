import datetime
from sqlalchemy.orm import Session
from app.models import DailySendCounter, SuppressionList
from app.config import settings

class GuardrailsService:
    @staticmethod
    def get_today_str() -> str:
        return datetime.datetime.utcnow().strftime("%Y-%m-%d")

    @classmethod
    def check_suppression(cls, db: Session, email: str) -> tuple[bool, str]:
        """
        Checks if the recipient email or domain is on the suppression list.
        Returns (is_suppressed, reason).
        """
        domain = email.split("@")[-1].lower() if "@" in email else ""
        
        # Check explicit email match
        suppressed_email = db.query(SuppressionList).filter(SuppressionList.email.ilike(email)).first()
        if suppressed_email:
            return True, f"Email '{email}' is explicitly on suppression list ({suppressed_email.reason})"

        # Check domain match
        if domain:
            suppressed_domain = db.query(SuppressionList).filter(SuppressionList.domain.ilike(domain)).first()
            if suppressed_domain:
                return True, f"Domain '@{domain}' is on suppression list ({suppressed_domain.reason})"

        return False, ""

    @classmethod
    def check_daily_send_cap(cls, db: Session) -> tuple[bool, int, int]:
        """
        Checks if today's daily send cap has been reached.
        Returns (can_send, send_count, daily_cap).
        """
        today = cls.get_today_str()
        counter = db.query(DailySendCounter).filter(DailySendCounter.date_str == today).first()
        
        if not counter:
            counter = DailySendCounter(date_str=today, send_count=0, daily_cap=settings.DAILY_SEND_CAP)
            db.add(counter)
            db.commit()
            db.refresh(counter)

        can_send = counter.send_count < counter.daily_cap
        return can_send, counter.send_count, counter.daily_cap

    @classmethod
    def increment_daily_send_count(cls, db: Session) -> int:
        """
        Increments today's send count.
        """
        today = cls.get_today_str()
        counter = db.query(DailySendCounter).filter(DailySendCounter.date_str == today).first()
        if not counter:
            counter = DailySendCounter(date_str=today, send_count=1, daily_cap=settings.DAILY_SEND_CAP)
            db.add(counter)
        else:
            counter.send_count += 1
        db.commit()
        db.refresh(counter)
        return counter.send_count

    @classmethod
    def get_guardrail_status(cls, db: Session) -> dict:
        today = cls.get_today_str()
        can_send, send_count, daily_cap = cls.check_daily_send_cap(db)
        suppressed_count = db.query(SuppressionList).count()
        
        return {
            "date": today,
            "send_count": send_count,
            "daily_cap": daily_cap,
            "remaining_sends": max(0, daily_cap - send_count),
            "suppressed_emails_count": suppressed_count,
            "is_cap_reached": not can_send
        }
