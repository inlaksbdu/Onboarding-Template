from loguru import logger
from datetime import timedelta, datetime, UTC
import jwt
from Library.config import settings
from uuid import uuid4


def create_access_token(data: dict, refresh: bool = False) -> str:
    to_encode = data.copy()
    if not refresh:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "refresh": refresh, "jti": str(uuid4())})
    encoded_jwt: str = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """Decode the access token and return the payload if valid, else return None."""
    try:
        decoded_token: dict = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return decoded_token
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        logger.error("Token has expired or is invalid")
        return None
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        raise e