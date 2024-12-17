import secrets
from typing import Any, Dict, Literal
from datetime import UTC, datetime, timedelta
from typing import Optional
from fastapi import HTTPException
from jose import jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext
from fastapi import status

from library.config import settings


class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    @staticmethod
    def create_access_token(
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

    @staticmethod
    def create_refresh_token(data: Dict[Literal["sub", "role"], str]) -> str:
        expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
        to_encode = {
            **data,
            "exp": expire,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32),
        }
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def decode_token(token: str, is_access: bool = True) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
            if payload["type"] != ("access" if is_access else "refresh"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
