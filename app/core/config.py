from pydantic_settings import BaseSettings
from typing import List, Optional, Dict
from functools import lru_cache
import secrets

class Settings(BaseSettings):
    PROJECT_NAME: str = "Banking Customer Onboarding"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    
    # External Services
    # OCR Services
    MICROSOFT_COMPUTER_VISION_KEY: str
    MICROSOFT_COMPUTER_VISION_ENDPOINT: str
    GOOGLE_CLOUD_VISION_CREDENTIALS: Dict
    
    # Face Recognition
    AZURE_FACE_KEY: str
    AZURE_FACE_ENDPOINT: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    
    # Document Verification
    JUMIO_API_TOKEN: str
    JUMIO_API_SECRET: str
    ONFIDO_API_TOKEN: str
    
    # Credit Bureau
    EXPERIAN_USERNAME: str
    EXPERIAN_PASSWORD: str
    EXPERIAN_CLIENT_ID: str
    EQUIFAX_API_KEY: str
    EQUIFAX_API_SECRET: str
    
    # AML Screening
    REFINITIV_USERNAME: str
    REFINITIV_PASSWORD: str
    REFINITIV_APP_KEY: str
    LEXISNEXIS_ACCESS_KEY: str
    LEXISNEXIS_SECRET: str
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Feature Flags
    ENABLE_BACKGROUND_TASKS: bool = True
    ENABLE_WEBHOOK_NOTIFICATIONS: bool = True
    
    class Config:
        case_sensitive = True
        env_file = ".env"

    def init(self, **kwargs):
        super().init(**kwargs)
        self.SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        )

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()