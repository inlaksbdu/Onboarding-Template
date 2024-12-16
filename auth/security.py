import secrets
from typing import TYPE_CHECKING, Any, Dict, Literal, Union
from datetime import UTC, datetime, timedelta
from typing import Optional
import uuid
from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext
from db.models.user import User
from db.models.refresh import RefreshToken
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from sqlalchemy import select

from library.config import settings


class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._failed_login_attempts: Dict[str, list[datetime]] = {}

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def create_access_token(
        self,
        data: Dict[Literal["sub", "role"], str],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode = {
            **data,
            "exp": expire,
            "type": "access",
            "jti": secrets.token_urlsafe(32),
        }
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    def create_refresh_token(self, data: Dict[Literal["sub", "role"], str]) -> str:
        expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
        to_encode = {
            **data,
            "exp": expire,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32),
        }
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    def check_login_attempts(self, email: str) -> None:
        now = datetime.now(UTC)
        attempts = self._failed_login_attempts.get(email, [])

        # Remove attempts older than lockout period
        valid_attempts = [
            attempt
            for attempt in attempts
            if now - attempt < timedelta(minutes=settings.login_attempt_lockout_minutes)
        ]

        if len(valid_attempts) >= settings.max_login_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please try again in {settings.login_attempt_lockout_minutes} minutes.",
            )

        self._failed_login_attempts[email] = valid_attempts

    def record_failed_attempt(self, email: str) -> None:
        attempts = self._failed_login_attempts.get(email, [])
        attempts.append(datetime.now(UTC))
        self._failed_login_attempts[email] = attempts

    def clear_login_attempts(self, email: str) -> None:
        self._failed_login_attempts.pop(email, None)

    # def generate_mfa_secret(self) -> str:
    #     return pyotp.random_base32()

    # def verify_mfa_token(self, secret: str, token: str) -> bool:
    #     totp = pyotp.TOTP(secret)
    #     return totp.verify(token)

    async def authenticate_user(
        self, session: AsyncSession, email: str, password: str
    ) -> Optional[User]:
        query = select(User).where(User.email == email, User.is_active == True)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    async def create_user_tokens(
        self, session: AsyncSession, user: User
    ) -> tuple[str, str]:
        access_token = self.create_access_token(
            data={"sub": user.email, "role": user.role}
        )

        refresh_token_str = self.create_refresh_token(
            data={"sub": user.email, "role": user.role}
        )
        refresh_token = RefreshToken(
            token=refresh_token_str,
            user_id=user.id,
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.refresh_token_expire_days),
        )

        session.add(refresh_token)
        await session.commit()

        return access_token, refresh_token_str

    async def create_new_user(self, session: AsyncSession, user: User) -> User:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
