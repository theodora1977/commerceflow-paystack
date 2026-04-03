from pydantic import SecretStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # =========================
    # APP CONFIG
    # =========================
    APP_NAME: str = "CommerceFlow API"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    APP_URL: str = Field(default="http://127.0.0.1:8000", validation_alias="APP_URL")

    # =========================
    # PAYSTACK CONFIG
    # =========================
    PAYSTACK_SECRET_KEY: SecretStr
    PAYSTACK_PUBLIC_KEY: Optional[str] = None
    PAYSTACK_BASE_URL: str = "https://api.paystack.co"

    # =========================
    # JWT CONFIG
    # =========================
    JWT_SECRET_KEY: SecretStr = Field(default="supersecretkey")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./commerceflow.db"

    @field_validator("PAYSTACK_SECRET_KEY")
    @classmethod
    def validate_paystack_key(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value().startswith("sk_"):
            raise ValueError("Paystack Secret Key must start with 'sk_'. Please check your .env file.")
        return v

    @field_validator("PAYSTACK_PUBLIC_KEY")
    @classmethod
    def validate_paystack_public_key(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("pk_"):
            raise ValueError("Paystack Public Key must start with 'pk_'. Please check your .env file.")
        return v

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()