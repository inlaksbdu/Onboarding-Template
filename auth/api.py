from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from auth.dependencies import (
    create_new_user,
    authenticate_user,
    create_user_tokens,
    get_refresh_token,
    get_user_by_email,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    get_current_active_user,
)
from db.session import get_session
from .security import AuthService
from .dto import Token, TokenPayload, UserCreate, UserResponse
from db.models.user import User


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_model: UserCreate,
    db: AsyncSession = Depends(get_session),
):
    user = await create_new_user(db, user_model)
    return user


@router.post("/token", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    # auth_deps.check_login_attempts(form_data.username)
    try:
        user = await authenticate_user(db, form_data.username, form_data.password)
        if not user:
            # auth_deps.record_failed_attempt(form_data.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # auth_deps.clear_login_attempts(form_data.username)
        logger.debug(f"User {user.email} logged in")
        access_token, refresh_token = await create_user_tokens(db, user)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=1800,  # 30 minutes
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=604800,  # 7 days
        )

        return Token(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    payload: TokenPayload,
    db: AsyncSession = Depends(get_session),
):
    try:
        token_data = AuthService.decode_token(payload.refresh_token, is_access=False)
        refresh_token = await get_refresh_token(db, payload.refresh_token)

        if not refresh_token or refresh_token.is_revoked:
            if refresh_token and refresh_token.user_id:
                await revoke_all_refresh_tokens(db, refresh_token.user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token",
            )

        if refresh_token.expires_at < datetime.now(UTC):
            await revoke_refresh_token(db, payload.refresh_token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
            )

        user = await get_user_by_email(db, token_data["sub"])
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User inactive or deleted",
            )

        access_token, new_refresh_token = await create_user_tokens(db, user)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=1800,  # 30 minutes
        )
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=604800,  # 7 days
        )

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    try:
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token:
            await revoke_refresh_token(db, refresh_token)
            if current_user:
                logger.debug(f"User {current_user.email} logged out")

        response.delete_cookie(
            key="access_token", httponly=True, secure=True, samesite="lax"
        )
        response.delete_cookie(
            key="refresh_token", httponly=True, secure=True, samesite="lax"
        )

        return {"message": "Successfully logged out"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    print(current_user)
    return current_user
