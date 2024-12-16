from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional
from jose import jwt, JWTError
from db.models.refresh import RefreshToken
from db.session import Database
from .security import AuthService
from .config import AuthConfig
from db.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class AuthDependencies:
    def __init__(self, db: Database, auth_service: AuthService):
        self.db = db
        self.auth_service = auth_service

    async def get_current_user(
        self,
        token: Annotated[str, Depends(oauth2_scheme)],
    ) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(
                token,
                self.auth_service.config.SECRET_KEY,
                algorithms=[self.auth_service.config.ALGORITHM],
            )
            email: str | None = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        query = select(User).where(User.email == email, User.is_active == True)

        async with self.db.session() as session:
            result = await session.execute(query)
            user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception
        return user

    async def get_current_active_admin(
        self, current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        return current_user

    async def get_user_by_email(
        self, session: AsyncSession, email: str
    ) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_refresh_token(
        self, session: AsyncSession, token: str
    ) -> Optional[RefreshToken]:
        query = select(RefreshToken).where(RefreshToken.token == token)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, session: AsyncSession, token: str) -> None:
        query = select(RefreshToken).where(RefreshToken.token == token)
        result = await session.execute(query)
        refresh_token = result.scalar_one_or_none()
        if refresh_token:
            refresh_token.is_revoked = True
            await session.commit()

    async def revoke_refresh_token_by_user_id(
        self, session: AsyncSession, user_id: int
    ) -> None:
        query = select(RefreshToken).where(RefreshToken.user_id == user_id)
        result = await session.execute(query)
        refresh_tokens = result.scalars().all()
        for refresh_token in refresh_tokens:
            refresh_token.is_revoked = True
        await session.commit()

    async def revoke_all_refresh_tokens(
        self, session: AsyncSession, user_id: int
    ) -> None:
        query = select(RefreshToken).where(RefreshToken.user_id == user_id)
        result = await session.execute(query)
        refresh_tokens = result.scalars().all()
        for refresh_token in refresh_tokens:
            await session.delete(refresh_token)
        await session.commit()

    async def revoke_all_refresh_tokens_except_current(
        self, session: AsyncSession, user_id: int, current_token: str
    ) -> None:
        query = select(RefreshToken).where(RefreshToken.user_id == user_id)
        result = await session.execute(query)
        refresh_tokens = result.scalars().all()
        for refresh_token in refresh_tokens:
            if refresh_token.token != current_token:
                await session.delete(refresh_token)
        await session.commit()
