from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    # Application
    APP_NAME: str = "Go Chicken API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # PostgreSQL (asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/go_chicken"

    # IoT Thresholds
    TEMPERATURE_ALERT_THRESHOLD: float = 35.0  # Celsius — triggers driver alert above this

    # Ollama AI
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    OLLAMA_CHAT_MODEL: str = "mistral"  # or any local 7B model
    OLLAMA_CONFIDENCE_THRESHOLD: float = 0.6  # Below this → fall back to regex

    # WhatsApp Cloud API (Meta)
    WHATSAPP_VERIFY_TOKEN: str = "gochicken123"
    WHATSAPP_API_TOKEN: str = ""            # Meta Graph API access token (for sending replies)
    WHATSAPP_PHONE_NUMBER_ID: str = ""      # Your WhatsApp Business phone number ID

    # Cloudinary (profile picture uploads)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    # Pricing (₹ per kg) — used for auto-replies and order totals
    PRICE_LIVE_BIRD: float = 180.00
    PRICE_DRESSED: float = 250.00
    PRICE_SKINLESS: float = 320.00

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
