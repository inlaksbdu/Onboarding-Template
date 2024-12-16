from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
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
    db_host: str
    db_username: str
    db_password: str
    db_name: str
    db_port: str
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

    model_config = SettingsConfigDict(
        **{
            "case_sensitive": False,
            "extra": "ignore",
            "env_prefix": ".env",
            "env_file_encoding": "utf-8",
        }
    )

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = BaseConfig()  # type: ignore
