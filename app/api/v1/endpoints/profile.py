from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from typing import List

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.customer import Customer
from app.models.document import Document
from app.models.verification_log import VerificationLog
from app.schemas.customer import CustomerUpdate, CustomerResponse
from app.schemas.document import DocumentResponse
from app.schemas.verification import VerificationLogResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/me", response_model=CustomerResponse)
async def get_current_customer_profile(
    current_user: Customer = Depends(get_current_active_user)
):
    """Get current customer profile."""
    return current_user

@router.put("/me", response_model=CustomerResponse)
async def update_customer_profile(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_active_user),
    customer_in: CustomerUpdate
):
    """Update current customer profile."""
    try:
        # Update customer fields
        for field, value in customer_in.dict(exclude_unset=True).items():
            setattr(current_user, field, value)
            
        await db.commit()
        await db.refresh(current_user)
        
        logger.info(f"Profile updated for customer {current_user.email}")
        return current_user
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating profile"
        )

@router.get("/me/documents", response_model=List[DocumentResponse])
async def get_customer_documents(
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_active_user)
):
    """Get all documents uploaded by current customer."""
    try:
        result = await db.execute(
            select(Document)
            .where(Document.customer_id == current_user.id)
            .order_by(Document.created_at.desc())
        )
        documents = result.scalars().all()
        return documents
        
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching documents"
        )

@router.get("/me/verification-logs", response_model=List[VerificationLogResponse])
async def get_verification_logs(
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_active_user)
):
    """Get verification history for current customer."""
    try:
        result = await db.execute(
            select(VerificationLog)
            .where(VerificationLog.customer_id == current_user.id)
            .order_by(VerificationLog.created_at.desc())
        )
        logs = result.scalars().all()
        return logs
        
    except Exception as e:
        logger.error(f"Error fetching verification logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching verification logs"
        )
