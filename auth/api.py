from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from db.session import Database
from .security import AuthService
from .schemas import Token, TokenPayload, UserCreate, UserResponse
from db.models.user import User

from library.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

db_obj = Database(settings.db_url)


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_model: UserCreate,
    session: Annotated[AsyncSession, Depends(db_obj.session)],
    auth_service: Annotated[AuthService, Depends()],
):
    user = await session.get(User, user_model.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already registered",
        )

    user = User(**user_model.model_dump())
    user = await auth_service.create_new_user(session, user)

    return user


@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(db_obj.session)],
    auth_service: Annotated[AuthService, Depends()],
):
    user = await auth_service.authenticate_user(
        session, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token = await auth_service.create_user_tokens(session, user)

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    payload: TokenPayload,
    session: Annotated[AsyncSession, Depends(db_obj.session)],
    auth_service: Annotated[AuthService, Depends()],
):
    query = select(RefreshToken).where(
        RefreshToken.token == payload.refresh_token,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow(),
    )
    result = await session.execute(query)
    refresh_token = result.scalar_one_or_none()

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Revoke the old refresh token
    refresh_token.is_revoked = True
    await session.commit()

    # Create new tokens
    access_token, new_refresh_token = await auth_service.create_user_tokens(
        session, refresh_token.user
    )

    return Token(
        access_token=access_token, refresh_token=new_refresh_token, token_type="bearer"
    )
