from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from typing import List
from datetime import datetime
import uuid
from fastapi.responses import JSONResponse

from app.core.security import get_current_active_user, get_password_hash
from app.db.session import get_db
from app.models.customer import Customer, VerificationStatus, CustomerStatus
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.verification_log import VerificationLog, VerificationType, VerificationResult
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.schemas.document import DocumentCreate, DocumentResponse
from app.core.verification import verify_document, verify_face
from app.services.jumio import JumioService
from app.services.azure_face import AzureFaceService
from app.services.refinitiv import RefinitivService
from app.services.experian import ExperianService
from app.services.ocr import OCRService
from app.core.exceptions import FaceVerificationError
from app.core.utils import calculate_risk_score, determine_risk_level, determine_customer_status

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def register_customer(
    *,
    db: AsyncSession = Depends(get_db),
    customer_in: CustomerCreate
):
    """Register a new customer."""
    try:
        # Check if email already exists
        result = await db.execute(
            select(Customer).where(Customer.email == customer_in.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        # Create new customer
        customer = Customer(
            **customer_in.dict(exclude={'password', 'confirm_password'}),
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        
        logger.info(f"New customer registered: {customer.email}")
        return customer
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )

@router.post("/onboard", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def onboard_customer(
    customer_data: CustomerCreate,
    id_document: UploadFile = File(...),
    selfie: UploadFile = File(...),
    video_stream: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Complete customer onboarding process with advanced verification steps:
    - OCR for document data extraction
    - Document verification through Jumio
    - Face detection, comparison, and liveness check through Azure Face API
    - AML screening through Refinitiv
    - Credit check through Experian
    """
    customer_id = str(uuid.uuid4())
    logger.info(f"Starting onboarding process for customer {customer_id}")
    
    try:
        async with (
            JumioService() as jumio_service,
            AzureFaceService() as face_service,
            OCRService() as ocr_service
        ):
            # 1. OCR Document Processing
            ocr_result = await ocr_service.extract_data(
                await id_document.read(),
                document_type=customer_data.document_type
            )
            logger.info(f"OCR completed for customer {customer_id}")
            
            # 2. Document verification through Jumio
            doc_verification = await jumio_service.verify_document({
                "customer_id": customer_id,
                "document": await id_document.read(),
                "document_type": customer_data.document_type,
                "ocr_data": ocr_result
            })
            logger.info(f"Document verification completed for customer {customer_id}")
            
            # 3. Face detection, comparison, and liveness check
            # First, verify face match between selfie and document
            face_match_result = await face_service.verify_face_match(
                await selfie.read(),
                await id_document.read()
            )
            
            if not face_match_result['success']:
                raise FaceVerificationError(face_match_result['message'])
            
            # Then perform liveness check
            liveness_result = await face_service.verify_liveness(
                await video_stream.read(),
                face_match_result['selfie_face_id']
            )
            logger.info(f"Face verification and liveness check completed for customer {customer_id}")
            
            # Create customer record with verification data
            customer = Customer(
                id=customer_id,
                **customer_data.dict(exclude={'document_type'}),
                document_data=doc_verification,
                ocr_data=ocr_result,
                face_verification_status=(
                    VerificationStatus.VERIFIED
                    if face_match_result['face_match']
                    else VerificationStatus.REJECTED
                ),
                face_match_score=face_match_result['face_match_score'],
                liveness_check_status=liveness_result.get('isLive', False),
                status=CustomerStatus.PENDING,
                document_type=customer_data.document_type,
                language_preference=customer_data.language_preference
            )
            
            # Save document record
            document = Document(
                customer_id=customer_id,
                document_type=customer_data.document_type,
                file_name=id_document.filename,
                file_type=id_document.content_type,
                verification_data=doc_verification,
                ocr_data=ocr_result,
                status=DocumentStatus.VERIFIED if doc_verification['success'] else DocumentStatus.REJECTED
            )
            
            # Create verification logs
            verification_logs = [
                VerificationLog(
                    customer_id=customer_id,
                    verification_type=VerificationType.DOCUMENT,
                    verification_service="jumio",
                    result=VerificationResult.SUCCESS if doc_verification['success'] else VerificationResult.FAILURE,
                    response_data=doc_verification
                ),
                VerificationLog(
                    customer_id=customer_id,
                    verification_type=VerificationType.FACE_MATCH,
                    verification_service="azure_face",
                    result=VerificationResult.SUCCESS if face_match_result['face_match'] else VerificationResult.FAILURE,
                    response_data=face_match_result
                ),
                VerificationLog(
                    customer_id=customer_id,
                    verification_type=VerificationType.LIVENESS,
                    verification_service="azure_face",
                    result=VerificationResult.SUCCESS if liveness_result.get('isLive') else VerificationResult.FAILURE,
                    response_data=liveness_result
                )
            ]
            
            # Save all records
            db.add(customer)
            db.add(document)
            for log in verification_logs:
                db.add(log)
                
            await db.commit()
            await db.refresh(customer)
            
            # Schedule background checks (AML and Credit)
            background_tasks.add_task(
                perform_background_checks,
                customer_id=customer_id,
                db=db
            )
            
            return CustomerResponse.from_orm(customer)
            
    except Exception as e:
        logger.error(f"Onboarding failed for customer {customer_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

async def perform_background_checks(customer_id: str, db: AsyncSession):
    """
    Perform background AML and Credit checks asynchronously
    """
    logger.info(f"Starting background checks for customer {customer_id}")
    
    try:
        result = await db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        async with RefinitivService() as aml_service, ExperianService() as credit_service:
            # AML screening
            aml_result = await aml_service.screen_customer({
                "name": customer.full_name,
                "date_of_birth": customer.date_of_birth,
                "nationality": customer.nationality,
                "document_data": customer.document_data
            })
            
            # Credit check
            credit_result = await credit_service.check_credit({
                "document_number": customer.document_number,
                "name": customer.full_name,
                "date_of_birth": customer.date_of_birth
            })
            
            # Create verification logs for background checks
            verification_logs = [
                VerificationLog(
                    customer_id=customer_id,
                    verification_type=VerificationType.AML,
                    verification_service="refinitiv",
                    result=VerificationResult.SUCCESS if aml_result["status"] == "PASS" else VerificationResult.FAILURE,
                    response_data=aml_result
                ),
                VerificationLog(
                    customer_id=customer_id,
                    verification_type=VerificationType.CREDIT,
                    verification_service="experian",
                    result=VerificationResult.SUCCESS if credit_result["status"] == "PASS" else VerificationResult.FAILURE,
                    response_data=credit_result
                )
            ]
            
            # Update customer record
            customer.aml_status = aml_result["status"]
            customer.credit_check_status = credit_result["status"]
            customer.risk_score = calculate_risk_score(aml_result, credit_result)
            customer.risk_level = determine_risk_level(customer.risk_score)
            customer.last_verified_at = datetime.utcnow()
            customer.status = determine_customer_status(
                aml_result["status"],
                credit_result["status"],
                customer.risk_score
            )
            
            # Save verification logs
            for log in verification_logs:
                db.add(log)
                
            await db.commit()
            logger.info(f"Background checks completed for customer {customer_id}")
            
    except Exception as e:
        logger.error(f"Background checks failed for customer {customer_id}: {str(e)}")
        await db.rollback()
        raise
