from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import logging

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    validate_refresh_token
)
from app.core.config import settings
from app.db.session import get_db
from app.schemas.auth import Token, RefreshToken
from app.models.customer import Customer
from sqlalchemy import select

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Login endpoint for customers."""
    try:
        # Find customer by email
        result = await db.execute(
            select(Customer).where(Customer.email == form_data.username)
        )
        customer = result.scalar_one_or_none()
        
        if not customer or not verify_password(form_data.password, customer.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Update last login
        customer.last_login = datetime.utcnow()
        await db.commit()
        
        # Create tokens
        access_token = create_access_token(customer.id)
        refresh_token = create_refresh_token(customer.id)
        
        logger.info(f"Customer {customer.email} logged in successfully")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token: RefreshToken,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        customer_id = validate_refresh_token(token.refresh_token)
        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
            
        # Verify customer still exists
        result = await db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
            
        # Create new tokens
        access_token = create_access_token(customer.id)
        refresh_token = create_refresh_token(customer.id)
        
        logger.info(f"Tokens refreshed for customer {customer.email}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while refreshing token"
        )
