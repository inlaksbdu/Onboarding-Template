from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict
from db.models.user import UserRole


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenPayload(BaseModel):
    refresh_token: str


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
