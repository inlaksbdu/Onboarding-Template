# for running alembic alone
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from loguru import logger


def load_environment_variables() -> str:
    load_dotenv(override=True)
    if (env := os.getenv("ENVIRONMENT")) == "production":
        logger.info(f"Environment: {env}")
        return ".env"
    elif env == "development":
        logger.info(f"Environment: {env}")
        load_dotenv(".env.dev", override=True)
        return ".env.dev"
    else:
        raise ValueError("Environment not set")


class AuthSettings(BaseSettings):
    database_host: str
    database_username: str
    database_password: str
    database_name: str
    database_port: int

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=load_environment_variables(),
        cache_strings="none",
    )

    @model_validator(mode="before")
    def validate_env_file(cls, v):
        if not v:
            raise ValueError("Environment file not found")
        return v

def get_auth_config() -> AuthSettings:
    return AuthSettings()








