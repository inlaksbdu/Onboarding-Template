from typing import TYPE_CHECKING
from datetime import UTC, datetime, timedelta
from typing import Optional
import uuid
from jose import jwt
from passlib.context import CryptContext
from db.models.user import User
from db.models.refresh import RefreshToken
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

if TYPE_CHECKING:
    from config import AuthConfig


class AuthService:
    def __init__(self, config: "AuthConfig"):
        self.config = config
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        return jwt.encode(
            to_encode, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM
        )

    def create_refresh_token(self) -> str:
        return jwt.encode(
            {"jti": str(uuid.uuid4())},
            self.config.SECRET_KEY,
            algorithm=self.config.ALGORITHM,
        )

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

        refresh_token_str = self.create_refresh_token()
        refresh_token = RefreshToken(
            token=refresh_token_str,
            user_id=user.id,
            expires_at=datetime.now(UTC)
            + timedelta(days=self.config.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        session.add(refresh_token)
        await session.commit()

        return access_token, refresh_token_str

    async def create_new_user(self, session: AsyncSession, user: User) -> User:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
