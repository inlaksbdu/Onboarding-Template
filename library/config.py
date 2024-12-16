from pydantic_settings import BaseSettings, SettingsConfigDict
from .utils import get_env_file


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
            "env_prefix": get_env_file(),
            "env_file_encoding": "utf-8",
        }
    )

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = BaseConfig()  # type: ignore
