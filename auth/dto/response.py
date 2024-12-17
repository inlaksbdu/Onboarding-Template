from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from .request import UserBase


class UserResponse(UserBase):
    id: UUID
    is_logged_in: bool
    is_active: bool
    is_verified: bool
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("last_login", "created_at", "updated_at", mode="before")
    @classmethod
    def convert_dates(cls, v):
        if (not v is None) and not isinstance(v, datetime):
            return datetime.fromisoformat(v)
        return v


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
