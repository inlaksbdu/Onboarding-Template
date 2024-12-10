from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from typing import Dict
from dependency_injector.wiring import inject, Provide

from bootstrap.container import Container
from Customer.services.verification_service import VerificationService, VerificationResult
from Customer.dto.requests.customer_request import CustomerCreateRequest

router = APIRouter(
    prefix="/verify",
    tags=["Customer Verification"]
)

@router.post("/document")
@inject
async def verify_document(
    document: UploadFile = File(...),
    verification_service: VerificationService = Depends(Provide[Container.verification_service])
) -> VerificationResult:
    """
    Verify uploaded ID document
    - Extracts information using Claude OCR
    - Verifies with National ID Database
    - Performs AML and Credit checks
    """
    content = await document.read()
    return await verification_service.verify_document(content)

@router.post("/biometrics")
@inject
async def verify_biometrics(
    selfie: UploadFile = File(...),
    id_photo: UploadFile = File(...),
    verification_service: VerificationService = Depends(Provide[Container.verification_service])
) -> VerificationResult:
    """
    Verify user's biometric information
    - Performs liveness detection
    - Compares selfie with ID photo
    """
    selfie_content = await selfie.read()
    id_photo_content = await id_photo.read()
    return await verification_service.verify_biometrics(selfie_content, id_photo_content)

@router.post("/complete")
@inject
async def complete_verification(
    document: UploadFile = File(...),
    selfie: UploadFile = File(...),
    verification_service: VerificationService = Depends(Provide[Container.verification_service])
) -> Dict[str, VerificationResult]:
    """
    Complete full verification process
    - Document verification
    - Biometric verification
    Returns results for each verification stage
    """
    document_content = await document.read()
    selfie_content = await selfie.read()
    return await verification_service.complete_verification(document_content, selfie_content)
