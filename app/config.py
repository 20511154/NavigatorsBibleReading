import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    telegram_token: str
    
    # Database
    database_url: str
    
    # Default settings
    default_tz: str = "Asia/Singapore"
    start_at_month: int = 1
    start_at_day: int = 1
    
    # Webhook
    webhook_base_url: str
    
    # Cron security
    cron_secret: str
    
    # Bot settings
    max_breaks_per_30_days: int = 5
    plan_days_per_month: int = 25
    plan_months: int = 12
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()