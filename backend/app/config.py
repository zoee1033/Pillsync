import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure .env is explicitly loaded into os.environ at module import
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Vision AI & Fusion Settings
    USE_GEMMA: bool = True
    VISION_PROVIDER: str = "gemma"
    FUSION_MODE: str = "always"

    # SMTP / Email Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_SENDER: str = os.getenv("SMTP_SENDER", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")

    OPENROUTER_API_KEY: str = ""
    GEMMA_MODEL: str = "google/gemma-3-27b-it"
    GEMMA_TIMEOUT: int = 20
    GEMMA_MAX_RETRIES: int = 1

    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Centralized Production Logging Flags
    LOG_LEVEL: str = "INFO"
    SQL_ECHO: bool = False
    ENABLE_VERBOSE_OCR_LOGS: bool = False
    ENABLE_VERBOSE_NOTIFICATION_LOGS: bool = False
    ENABLE_VERBOSE_POLLING_LOGS: bool = False
    ENABLE_VERBOSE_FIREBASE_LOGS: bool = False
    ENABLE_VERBOSE_WEBSOCKET_LOGS: bool = False
    ENABLE_VERBOSE_SCHEDULER_LOGS: bool = False
    ENABLE_VERBOSE_SQL_LOGS: bool = False

    model_config = SettingsConfigDict(
        env_file=env_path,
        extra="ignore"
    )


settings = Settings()