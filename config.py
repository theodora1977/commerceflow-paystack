import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # =========================
    # APP CONFIG
    # =========================
    APP_NAME: str = "E-Commerce FastAPI Backend"
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"

    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8000))

    # =========================
    # PAYSTACK CONFIG
    # =========================
    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_PUBLIC_KEY: str = os.getenv("PAYSTACK_PUBLIC_KEY", "")
    PAYSTACK_BASE_URL: str = os.getenv(
        "PAYSTACK_BASE_URL", "https://api.paystack.co"
    )

    # Webhook uses same secret key
    PAYSTACK_WEBHOOK_SECRET: str = os.getenv(
        "PAYSTACK_SECRET_KEY", ""
    )

    # =========================
    # JWT CONFIG
    # =========================
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "supersecretkey")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    )

    # =========================
    # DATABASE (OPTIONAL)
    # =========================
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")


settings = Settings()


# =========================
# VALIDATION (Fail fast)
# =========================
def validate_settings():
    if not settings.PAYSTACK_SECRET_KEY:
        raise ValueError("PAYSTACK_SECRET_KEY is not set")

    if not settings.JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY is not set")


validate_settings()