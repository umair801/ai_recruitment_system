"""
Configuration management for AI Recruitment System
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    db_pool_size: int = Field(10, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(20, env="DB_MAX_OVERFLOW")
    
    # Email Configuration
    smtp_host: str = Field("smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: str = Field(..., env="SMTP_USERNAME")
    smtp_password: str = Field(..., env="SMTP_PASSWORD")
    from_email: str = Field(..., env="FROM_EMAIL")
    
    # Calendar
    google_calendar_credentials_path: str = Field(
        "./config/google_credentials.json",
        env="GOOGLE_CALENDAR_CREDENTIALS_PATH"
    )
    google_calendar_token_path: str = Field(
        "./config/token.json",
        env="GOOGLE_CALENDAR_TOKEN_PATH"
    )
    
    # Video Platform
    video_platform: str = Field("zoom", env="VIDEO_PLATFORM")
    zoom_api_key: Optional[str] = Field(None, env="ZOOM_API_KEY")
    zoom_api_secret: Optional[str] = Field(None, env="ZOOM_API_SECRET")
    
    # AWS
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("us-east-1", env="AWS_REGION")
    s3_bucket_name: Optional[str] = Field(None, env="S3_BUCKET_NAME")
    
    # Application
    app_name: str = Field("AI Recruitment System", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    allowed_origins: str = Field("http://localhost:3000", env="ALLOWED_ORIGINS")
    
    # Screening Thresholds
    min_resume_score: float = Field(0.45, env="MIN_RESUME_SCORE")
    strong_match_threshold: float = Field(0.75, env="STRONG_MATCH_THRESHOLD")
    proceed_to_interview_threshold: float = Field(0.60, env="PROCEED_TO_INTERVIEW_THRESHOLD")
    
    # Interview Settings
    video_interview_duration_minutes: int = Field(30, env="VIDEO_INTERVIEW_DURATION_MINUTES")
    min_interview_score: float = Field(7.5, env="MIN_INTERVIEW_SCORE")
    max_questions_per_interview: int = Field(7, env="MAX_QUESTIONS_PER_INTERVIEW")
    
    # Bias Mitigation
    enable_bias_auditing: bool = Field(True, env="ENABLE_BIAS_AUDITING")
    adverse_impact_threshold: float = Field(0.80, env="ADVERSE_IMPACT_THRESHOLD")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    max_concurrent_interviews: int = Field(5, env="MAX_CONCURRENT_INTERVIEWS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


# Directory paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RESUME_DIR = DATA_DIR / "resumes"
JOB_DESC_DIR = DATA_DIR / "job_descriptions"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for directory in [DATA_DIR, RESUME_DIR, JOB_DESC_DIR, MODELS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
