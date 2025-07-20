"""
Core configuration for RushJob backend.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App config
    app_name: str = "RushJob"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str = Field(..., description="PostgreSQL connection string")
    
    # Supabase
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase anonymous key")
    supabase_service_key: str = Field(..., description="Supabase service role key")
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Job Polling
    default_poll_interval_minutes: int = 15
    max_concurrent_polls: int = 5
    request_timeout_seconds: int = 30
    
    # Rate Limiting
    greenhouse_rate_limit_per_minute: int = 60
    max_retries: int = 3
    retry_backoff_seconds: int = 5
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()