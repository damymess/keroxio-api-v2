"""
Configuration - loads from environment variables
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Keroxio API"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/keroxio")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "https://keroxio.fr",
        "https://app.keroxio.fr",
        "https://admin.keroxio.fr",
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Resend (Email)
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@keroxio.fr")
    
    # AutoBG.ai (Image processing)
    AUTOBG_API_KEY: str = os.getenv("AUTOBG_API_KEY", "")
    
    # Remove.bg API
    REMOVEBG_API_KEY: str = os.getenv("REMOVEBG_API_KEY", "")
    
    # Storage
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "/app/storage")
    STORAGE_URL: str = os.getenv("STORAGE_URL", "https://storage.keroxio.fr")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
