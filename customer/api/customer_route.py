from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    status,
    BackgroundTasks,
    Depends,
)
from fastapi.responses import ORJSONResponse
from typing import Annotated, Optional, Dict
from dependency_injector.wiring import inject, Provide
import uuid
from loguru import logger
from datetime import datetime

import orjson

from bootstrap.container import Container
from customer.services.customer_service import CustomerService
from customer.services.verification_service import VerificationService
from customer.dto.requests.customer_request import (
    CustomerCreateRequest,
)
from customer.dto.response.customer_response import CustomerResponse

router = APIRouter(prefix="/customer", tags=["Customer Management"])

# Store registration sessions in memory (in production, use Redis/DB)
registration_sessions = {}


@router.post(
    "/card-ocr",
    status_code=status.HTTP_200_OK,
    response_class=ORJSONResponse,
    summary="Extract information from ID cards and initiate registration",
    description="Upload ID documents and start the registration process",
)
@inject
async def extract_document_info(
    front: UploadFile = File(
        ..., description="1-2 document images to process", media_type="image/*"
    ),
    back: Annotated[UploadFile, Optional] = File(
        None, description="Optional second document image", media_type="image/*"
    ),
    verification_service: VerificationService = Depends(
        Provide[Container.verification_service]
    ),
):
    """
    Step 1: Document Upload and Information Extraction
    - Extracts information from documents using Claude
    - Stores documents in S3
    - Creates registration session
    """

    allowed_types = {"image/jpeg", "image/png", "image/gif"}
    not_img = next(
        (
            file
            for file in (front, back)
            if (not file is None) and (file.content_type not in allowed_types)
        ),
        None,
    )
    if not_img:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only image files are allowed. Invalid file: {not_img.filename}",
        )
    try:
        images = [await doc.read() for doc in (front, back) if doc]
        result = await verification_service.verify_document(document_images=images)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result.message
            )

        session_id = str(uuid.uuid4())

        registration_sessions[session_id] = {
            "id_card_info": result.details,
            "id_photo_path": result.details["images_path"][
                0
            ],  # S3 key for face comparison
            "status": "documents_verified",
            "created_at": datetime.now().isoformat(),
        }

        return ORJSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "data": result.details,
                "session_id": session_id,
            },
        )

    except Exception as e:
        logger.error(f"Document extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing documents: {str(e)}",
        )


@router.post("/verify-face/{session_id}")
@inject
async def verify_face(
    session_id: str,
    selfie: UploadFile = File(...),
    verification_service: VerificationService = Depends(
        Provide[Container.verification_service]
    ),
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
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid session ID"
            )

        session = registration_sessions[session_id]
        if session["status"] != "documents_verified":
            logger.error(
                f"Invalid session status for face verification: {session['status']}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Documents must be verified before face verification",
            )

        # Process selfie
        logger.info("Processing selfie image")
        selfie_bytes = await selfie.read()
        face_result = await verification_service.verify_biometrics(
            selfie_bytes,
            session["id_photo_path"],  # Using ID photo path for comparison
        )

        if not face_result.success:
            logger.error(f"Face verification failed: {face_result.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Face verification failed: {face_result.message}",
            )

        # Update session
        session["status"] = "face_verified"
        session["selfie_path"] = face_result.details["selfie_path"]
        session["face_match_score"] = face_result.details["face_match_score"]

        logger.success(f"Face verification completed for session: {session_id}")
        return {
            "status": "success",
            "message": "Face verification successful",
            "match_score": face_result.details["face_match_score"],
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
    verification_service: VerificationService = Depends(
        Provide[Container.verification_service]
    ),
    customer_service: CustomerService = Depends(Provide[Container.customer_service]),
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
                detail="Invalid or expired session",
            )

        session = registration_sessions[session_id]
        if session["status"] != "face_verified":
            logger.error(
                f"Invalid session status for registration: {session['status']}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Complete document and face verification first",
            )

        # Create customer with verified information
        logger.info("Completing verification and creating customer record")
        result = await verification_service.complete_verification(
            session=session, customer_data=customer_data
        )

        if not result.success:
            logger.error(f"Registration failed: {result.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result.message
            )

        # Create customer record
        customer_response = await customer_service.create_customer(customer_data)

        # Clean up session in background
        background_tasks.add_task(registration_sessions.pop, session_id, None)

        logger.success(
            f"Customer registration completed. Customer ID: {customer_response.customer_id}"
        )
        return customer_response

    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
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
                detail="Invalid or expired session",
            )

        session = registration_sessions[session_id]

        logger.info(f"Retrieved status for session {session_id}: {session['status']}")
        return {
            "status": session["status"],
            "document_info": session.get("document_info"),
            "has_additional_doc": "document2_info" in session,
            "has_selfie": "selfie_path" in session,
        }

    except Exception as e:
        logger.error(f"Failed to get registration status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
