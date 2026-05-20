from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    GOOGLE_SERVICE_ACCOUNT_EMAIL: str
    GOOGLE_PRIVATE_KEY: str
    GOOGLE_SHEET_ID: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    
    BUSINESS_NAME: str = "Grooming Salon"
    TIMEZONE: str = "Europe/Belgrade"
    ENV: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()