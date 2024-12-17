from uuid import UUID
from datetime import UTC, datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional
from auth.dto.request import UserCreate
from db.models.refresh import RefreshToken
from .security import AuthService
from db.models.user import User, UserRole
from library.config import settings
from db.session import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
auth_service = AuthService()


async def get_current_user(
    db: AsyncSession = Depends(get_session),
    *,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = auth_service.decode_token(token, is_access=True)
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    if (exp := payload.get("exp")) and datetime.fromtimestamp(
        exp, tz=UTC
    ) < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(User.email == email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if user is None or user.role == UserRole.BANNED or not user.is_logged_in:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_active_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_new_user(db: AsyncSession, user: UserCreate) -> User:
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already registered",
        )
    new_user = User(
        email=user.email,
        phone=user.phone,
        role=user.role,
        hashed_password=auth_service.get_password_hash(user.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def get_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    query = select(RefreshToken).where(RefreshToken.token == token)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def revoke_refresh_token(db: AsyncSession, token: str) -> None:
    query = select(RefreshToken).where(RefreshToken.token == token)
    result = await db.execute(query)
    refresh_token = result.scalar_one_or_none()
    if refresh_token:
        refresh_token.user.is_logged_in = False
        refresh_token.is_revoked = True
        await db.commit()


async def revoke_refresh_token_by_user_id(db: AsyncSession, user_id: UUID) -> None:
    query = select(RefreshToken).where(RefreshToken.user_id == user_id)
    result = await db.execute(query)
    refresh_tokens = result.scalars().all()
    for refresh_token in refresh_tokens:
        refresh_token.is_revoked = True
    await db.commit()


async def revoke_all_refresh_tokens(db: AsyncSession, user_id: UUID) -> None:
    query = select(RefreshToken).where(RefreshToken.user_id == user_id)
    result = await db.execute(query)
    refresh_tokens = result.scalars().all()
    for refresh_token in refresh_tokens:
        await db.delete(refresh_token)
    await db.commit()


async def revoke_all_refresh_tokens_except_current(
    db: AsyncSession, user_id: UUID, current_token: str
) -> None:
    query = select(RefreshToken).where(RefreshToken.user_id == user_id)
    result = await db.execute(query)
    refresh_tokens = result.scalars().all()
    for refresh_token in refresh_tokens:
        if refresh_token.token != current_token:
            await db.delete(refresh_token)
    await db.commit()


# def check_login_attempts(email: str) -> None:
#     now = datetime.now(UTC)
#     attempts = _failed_login_attempts.get(email, [])

#     valid_attempts = [
#         attempt
#         for attempt in attempts
#         if now - attempt < timedelta(minutes=settings.login_attempt_lockout_minutes)
#     ]

#     if len(valid_attempts) >= settings.max_login_attempts:
#         raise HTTPException(
#             status_code=status.HTTP_429_TOO_MANY_REQUESTS,
#             detail=f"Too many failed login attempts. Please try again in {settings.login_attempt_lockout_minutes} minutes.",
#         )

#     self._failed_login_attempts[email] = valid_attempts


# def record_failed_attempt(email: str) -> None:
#     attempts = self._failed_login_attempts.get(email, [])
#     attempts.append(datetime.now(UTC))
#     self._failed_login_attempts[email] = attempts


# def clear_login_attempts(email: str) -> None:
#     self._failed_login_attempts.pop(email, None)


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    query = select(User).where(User.email == email, User.is_active == True)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        return None
    if not auth_service.verify_password(password, user.hashed_password):
        return None
    return user


async def create_user_tokens(db: AsyncSession, user: User) -> tuple[str, str]:
    access_token = auth_service.create_access_token(
        data={"sub": user.email, "role": user.role}
    )

    refresh_token_str = auth_service.create_refresh_token(
        data={"sub": user.email, "role": user.role}
    )
    refresh_token = RefreshToken(
        token=refresh_token_str,
        user_id=user.id,
        expires_at=datetime.now(UTC)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    user.is_logged_in = True
    user.last_login = datetime.now(UTC)
    db.add(refresh_token)
    await db.commit()

    return access_token, refresh_token_str
