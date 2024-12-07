from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.db.session import get_db
from app.models.customer import Customer

# Setup logging
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any]) -> str:
    """Create JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Customer:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        customer_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if customer_id is None:
            logger.error("JWT token missing 'sub' claim")
            raise credentials_exception
        if token_type != "access":
            logger.error("Invalid token type")
            raise credentials_exception
            
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception
        
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer is None:
        logger.error(f"User {customer_id} not found in database")
        raise credentials_exception
        
    return customer

async def get_current_active_user(
    current_user: Customer = Security(get_current_user),
) -> Customer:
    """Get current active user."""
    if current_user.verification_status == "rejected":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def validate_refresh_token(token: str) -> Optional[int]:
    """Validate refresh token and return user ID if valid."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        customer_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if customer_id is None or token_type != "refresh":
            return None
            
        return int(customer_id)
        
    except JWTError:
        return None