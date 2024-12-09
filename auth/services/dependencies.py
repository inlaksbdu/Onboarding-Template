from typing import Any, List
from fastapi.security.http import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request, HTTPException, status, Depends
from loguru import logger
from sqlalchemy.ext.asyncio.session import AsyncSession
from backend.auth.utils import decode_access_token
from backend.library.redis_services import is_jti_blacklisted
from backend.persistence.db.models.base import get_db
from backend.persistence.db.models.user import User


class AuthBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        creds = await super().__call__(request)
        if creds is None:
            return None
        token = creds.credentials
        if not (token_data := decode_access_token(token)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        if await is_jti_blacklisted(token_data["jti"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

        # self.verify_token(token_data)
        # logger.info(f"Token data: {token_data}")

        return token_data

    # def verify_token(self, token_data: dict) -> None:
    #     raise NotImplementedError


class AccessBearer(AuthBearer):
    def verify_token(self, token_data: dict) -> None:
        if token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )


class RefreshBearer(AuthBearer):
    def verify_token(self, token_data: dict) -> None:
        if not token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )


async def get_current_user(
    security: AccessBearer = Depends(AccessBearer()),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    return await db.get(User, security["id"])


class RoleChecker:
    def __init__(self, roles: List[str]):
        self.roles = roles

    async def __call__(self, user: User = Depends(get_current_user)) -> bool:
        if user.role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return True