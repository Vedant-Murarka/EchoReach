import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "EchoReach Backend API"
    VERSION: str = "1.0.0"
    
    # Database: SQLite (default) or Supabase PostgreSQL (e.g. postgresql://postgres:...@db...supabase.co:5432/postgres)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./echoreach.db")
    
    # LLM Providers (Gemini / Groq / Fallback)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Web Search Providers
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY", "")
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY", "")
    
    # Guardrails & Escalations
    DAILY_SEND_CAP: int = 50
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL", "")
    DISCORD_WEBHOOK_URL: Optional[str] = os.getenv("DISCORD_WEBHOOK_URL", "")
    
    # Server Config
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
