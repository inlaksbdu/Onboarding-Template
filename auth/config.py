from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthConfig(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_prefix=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_auth_config() -> AuthConfig:
    return AuthConfig()  # type: ignore
