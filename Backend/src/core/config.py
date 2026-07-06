from pydantic_settings import BaseSettings
from typing import Optional
import json
from pathlib import Path

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Free Commerce Platform"
    DEBUG: bool = False
    SECRET_KEY: str
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Stripe
    STRIPE_SECRET_KEY:Optional[str] = None
    STRIPE_WEBHOOK_SECRET:Optional[str] = None

    # M-Pesa
    MPESA_CONSUMER_KEY: Optional[str] = None
    MPESA_CONSUMER_SECRET: Optional[str] = None
    MPESA_SHORTCODE:str = "174379"
    MPESA_PASSKEY: Optional[str] = None
    MPESA_ENV:str = "sandbox"  
    MPESA_CALLBACK_URL: Optional[str] = None
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    
    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Commission
    DEFAULT_COMMISSION_PERCENTAGE: float = 10.0
    
    class Config:
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = True

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
           url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

settings = Settings()