from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from .utils import get_env_file


class BaseConfig(BaseSettings):
    environment: str = "development"
    db_host: str
    db_username: str
    db_password: str
    db_name: str
    db_port: str
    db_echo: bool = False
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    secret_key: str
    algorithm: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_bucket_name: str
    aws_region: str
    openai_api_key: str
    langchain_tracing_v2: bool
    langchain_api_key: str
    langchain_project: str
    anthropic_api_key: str
    # redirect_uri: str
    encryption_key: str
    # ngrok_url: str
    backend_url: str

    login_attempt_lockout_minutes: int = 15
    max_login_attempts: int = 5

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_prefix=".env",
        env_file_encoding="utf-8",
        cache_strings="none",
        env_file=get_env_file(),
    )

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = BaseConfig()  # type: ignore
