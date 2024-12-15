from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import os
from loguru import logger


def get_env_file():
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
    logger.info(f"Current environment: {ENVIRONMENT}")

    if ENVIRONMENT == "production":
        ENV_FILE = ".env"
    elif ENVIRONMENT == "development":
        ENV_FILE = ".env.dev"
    else:
        ENV_FILE = f".env.{ENVIRONMENT}" if ENVIRONMENT else ".env"

    logger.info(f"Using env file: {ENV_FILE}")

    if os.path.exists(ENV_FILE):
        load_dotenv(ENV_FILE, override=True)
        logger.info(f"Loaded environment variables from {ENV_FILE}")
    else:
        logger.info(
            f"Environment file {ENV_FILE} does not exist; using system environment variables."
        )

    return ENV_FILE


ENV_FILE = get_env_file()


class BaseConfig(BaseSettings):
    environment: str = "development"
    database_host: str
    database_username: str
    database_password: str
    database_name: str
    database_port: str
    # redis_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_bucket_name: str
    aws_region: str
    openai_api_key: str
    langchain_tracing_v2: bool
    langchain_api_key: str
    langchain_project: str
    anthropic_api_key: str
    groq_api_key: str
    unstructured_api_key: str
    tavily_api_key: str
    secret_key: str
    # redirect_uri: str
    encryption_key: str
    # ngrok_url: str
    backend_url: str

    class Config:
        env_file = ENV_FILE
        extra = "ignore"
        case_insensitive = True


settings = BaseConfig()
