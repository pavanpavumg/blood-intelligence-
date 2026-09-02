from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Blood Test Intelligence System"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # File Upload & Storage configuration
    MAX_UPLOAD_SIZE_MB: int = 20
    UPLOAD_DIR: str = "data/uploads"
    
    # Server configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    SECRET_KEY: str = "secret-key-change-in-production-32-bytes-long"
    
    # Database configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/blood_test_db"
    
    # Redis configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS Configuration
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings: Settings = Settings()
