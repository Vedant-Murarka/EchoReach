import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "EchoReach Backend API"
    VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite:///./echoreach.db"
    
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY", "")
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY", "")
    
    DAILY_SEND_CAP: int = 50
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL", "")
    DISCORD_WEBHOOK_URL: Optional[str] = os.getenv("DISCORD_WEBHOOK_URL", "")
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
