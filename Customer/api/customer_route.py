from fastapi import (
    APIRouter, 
    File, 
    UploadFile, 
    HTTPException, 
    status,
    BackgroundTasks,
    Depends
)
from typing import List, Optional, Dict
from dependency_injector.wiring import inject, Provide
import uuid
import logging
from loguru import logger
from datetime import datetime

from Library.utils import (
    MultiDocumentProcessor, 
    encode_image_to_base64,
    DocumentExtractionResult
)
from bootstrap.container import Container
from Customer.services.customer_service import CustomerService
from Customer.services.verification_service import VerificationService
from Customer.dto.requests.customer_request import CustomerCreateRequest, CustomerUpdateRequest
from Customer.dto.response.customer_response import CustomerResponse
from Customer.services.face_verification_service import FaceVerificationService

router = APIRouter(
    prefix="/customer",
    tags=["Customer Management"]
)

# Store registration sessions in memory (in production, use Redis/DB)
registration_sessions = {}

@router.post(
    "/extract-documents", 
    response_model=Dict,
    summary="Extract information from ID cards and initiate registration",
    description="Upload ID documents and start the registration process"
)
@inject
async def extract_document_info(
    documents: List[UploadFile] = File(..., description="1-2 document images to process"),
    document_types: Optional[List[str]] = None,
    verification_service: VerificationService = Depends(Provide[Container.verification_service])
):
    """
    Step 1: Document Upload and Information Extraction
    - Extracts information from documents using Claude
    - Stores documents in S3
    - Creates registration session
    """
    logger.info("Starting document extraction process")
    
    # Validate file inputs
    if len(documents) > 2:
        logger.error("Maximum 2 documents allowed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 2 documents allowed"
        )
    
    # Validate file types
    allowed_types = {'image/jpeg', 'image/png', 'image/gif'}
    for file in documents:
        if file.content_type not in allowed_types:
            logger.error(f"Unsupported file type: {file.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
    
    try:
        # Initialize services
        face_service = FaceVerificationService()
        
        # Process first document (ID Card)
        logger.info("Processing ID card")
        id_content = await documents[0].read()
        
        # Store ID card in S3
        id_key = f"documents/id_card_{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        id_path = await face_service.upload_to_s3(id_content, id_key)
        
        # Convert to base64 for OCR
        id_base64 = encode_image_to_base64(id_content)
        
        # Process documents
        processor = MultiDocumentProcessor()
        image_bases = [id_base64]
        doc_types = ["ID Card"]
        
        # Handle second document if provided
        birth_cert_path = None
        if len(documents) > 1:
            logger.info("Processing birth certificate")
            birth_content = await documents[1].read()
            
            # Store birth certificate in S3
            birth_key = f"documents/birth_cert_{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            birth_cert_path = await face_service.upload_to_s3(birth_content, birth_key)
            
            # Add to processing queue
            birth_base64 = encode_image_to_base64(birth_content)
            image_bases.append(birth_base64)
            doc_types.append("Birth Certificate")
        
        # Extract information from all documents
        results = await processor.process_documents(
            images=image_bases,
            document_types=doc_types
        )
        
        # Create registration session
        session_id = str(uuid.uuid4())
        logger.info(f"Creating registration session: {session_id}")
        
        # Store session data
        registration_sessions[session_id] = {
            "id_card_info": results[0].document_info.dict() if results[0].document_info else {},
            "id_photo_path": id_key,  # S3 key for face comparison
            "status": "documents_verified",
            "created_at": datetime.now().isoformat()
        }
        
        # Add birth certificate info if provided
        if birth_cert_path and len(results) > 1:
            registration_sessions[session_id]["birth_cert_info"] = (
                results[1].document_info.dict() if results[1].document_info else {}
            )
            registration_sessions[session_id]["birth_cert_path"] = birth_key
        
        logger.success(f"Document extraction completed for session: {session_id}")
        return {
            "session_id": session_id,
            "status": "success",
            "extracted_info": {
                "id_card": results[0].document_info.dict() if results[0].document_info else {},
                "birth_certificate": (
                    results[1].document_info.dict() if len(results) > 1 and results[1].document_info else None
                )
            }
        }
        
    except Exception as e:
        logger.error(f"Document extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing documents: {str(e)}"
        )

@router.post("/verify-face/{session_id}")
@inject
async def verify_face(
    session_id: str,
    selfie: UploadFile = File(...),
    verification_service: VerificationService = Depends(Provide[Container.verification_service])
) -> Dict:
    """
    Verify user's face against ID photo
    Assumes frontend has performed liveness check
    """
    logger.info(f"Starting face verification for session: {session_id}")
    try:
        if session_id not in registration_sessions:
            logger.error(f"Invalid session ID: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid session ID"
            )
            
        session = registration_sessions[session_id]
        if session["status"] != "documents_verified":
            logger.error(f"Invalid session status for face verification: {session['status']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Documents must be verified before face verification"
            )
        
        # Process selfie
        logger.info("Processing selfie image")
        selfie_bytes = await selfie.read()
        face_result = await verification_service.verify_biometrics(
            selfie_bytes,
            session["id_photo_path"]  # Using ID photo path for comparison
        )
        
        if not face_result.success:
            logger.error(f"Face verification failed: {face_result.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Face verification failed: {face_result.message}"
            )
            
        # Update session
        session["status"] = "face_verified"
        session["selfie_path"] = face_result.details["selfie_path"]
        session["face_match_score"] = face_result.details["face_match_score"]
        
        logger.success(f"Face verification completed for session: {session_id}")
        return {
            "status": "success",
            "message": "Face verification successful",
            "match_score": face_result.details["face_match_score"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Face verification failed: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/register/{session_id}", response_model=CustomerResponse)
@inject
async def register_customer(
    session_id: str,
    background_tasks: BackgroundTasks,
    customer_data: CustomerCreateRequest,
    verification_service: VerificationService = Depends(Provide[Container.verification_service]),
    customer_service: CustomerService = Depends(Provide[Container.customer_service])
) -> CustomerResponse:
    """
    Step 3: Complete Registration
    - Verify all steps are completed
    - Create customer record with verified information
    """
    logger.info(f"Starting customer registration for session: {session_id}")
    try:
        if session_id not in registration_sessions:
            logger.error(f"Invalid session ID: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired session"
            )
            
        session = registration_sessions[session_id]
        if session["status"] != "face_verified":
            logger.error(f"Invalid session status for registration: {session['status']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Complete document and face verification first"
            )
        
        # Create customer with verified information
        logger.info("Completing verification and creating customer record")
        result = await verification_service.complete_verification(
            session=session,
            customer_data=customer_data
        )
        
        if not result.success:
            logger.error(f"Registration failed: {result.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        # Create customer record
        customer_response = await customer_service.create_customer(customer_data)
        
        # Clean up session in background
        background_tasks.add_task(registration_sessions.pop, session_id, None)
        
        logger.success(f"Customer registration completed. Customer ID: {customer_response.customer_id}")
        return customer_response
        
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/registration-status/{session_id}")
async def get_registration_status(session_id: str) -> Dict:
    """Get current registration session status"""
    logger.info(f"Fetching registration status for session: {session_id}")
    try:
        if session_id not in registration_sessions:
            logger.error(f"Invalid session ID: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired session"
            )
            
        session = registration_sessions[session_id]
        
        logger.info(f"Retrieved status for session {session_id}: {session['status']}")
        return {
            "status": session["status"],
            "document_info": session.get("document_info"),
            "has_additional_doc": "document2_info" in session,
            "has_selfie": "selfie_path" in session
        }
        
    except Exception as e:
        logger.error(f"Failed to get registration status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )