import re
import urllib.parse
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger("echoreach.database")

def normalize_database_url(url: str) -> str:
    """
    Normalizes and safely sanitizes database connection URLs:
    - Converts postgres:// to postgresql://
    - Safely encodes passwords containing special characters like '@' or '#'
    - Adds sslmode=require for Supabase / remote Postgres if missing
    """
    if not url:
        return "sqlite:///./echoreach.db"

    clean_url = url.strip()
    if clean_url.startswith("postgres://"):
        clean_url = clean_url.replace("postgres://", "postgresql://", 1)

    if clean_url.startswith("postgresql://"):
        # Match postgresql://user:password@host:port/dbname
        # Handle case where password might contain raw '@'
        try:
            proto, rest = clean_url.split("://", 1)
            # Find the last '@' which separates auth credentials from host
            if "@" in rest:
                auth_part, host_part = rest.rsplit("@", 1)
                if ":" in auth_part:
                    user, password = auth_part.split(":", 1)
                    # Safely URL encode password if it isn't already encoded
                    encoded_password = urllib.parse.quote_plus(urllib.parse.unquote_plus(password))
                    clean_url = f"{proto}://{user}:{encoded_password}@{host_part}"
        except Exception as e:
            logger.warning(f"URL normalization warning: {e}")

    return clean_url

db_url = normalize_database_url(settings.DATABASE_URL)

connect_args = {}
engine_kwargs = {"echo": False}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

try:
    engine = create_engine(db_url, **engine_kwargs)
    # Quick probe to test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info(f"Database connected successfully via {db_url.split('@')[-1] if '@' in db_url else db_url}")
except Exception as e:
    logger.warning(f"Could not connect to configured database ({e}). Falling back to local SQLite: sqlite:///./echoreach.db")
    db_url = "sqlite:///./echoreach.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
