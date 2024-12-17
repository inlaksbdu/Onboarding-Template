from pydantic import BaseModel, EmailStr
from db.models.user import UserRole, AccountType


class TokenPayload(BaseModel):
    refresh_token: str


class UserBase(BaseModel):
    email: EmailStr
    phone: str
    account_type: AccountType
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    password: str
