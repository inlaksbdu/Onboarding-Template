from typing import Optional, Dict, List
import os
import io
import uuid
from datetime import datetime
import boto3
from fastapi import HTTPException
from pydantic import BaseModel
from loguru import logger

from Library.utils import DocumentOCRProcessor, DocumentExtractionResult
from Customer.services.face_verification_service import FaceVerificationService
from Customer.dto.requests.customer_request import CustomerCreateRequest
from persistence.db.models.customer import Customer


class VerificationResult(BaseModel):
    success: bool
    stage: str
    message: str
    details: Optional[Dict] = None


class BiometricVerificationResult(BaseModel):
    face_match_score: float
    success: bool
    message: str


class VerificationService:
    def __init__(self):
        logger.info("Initializing VerificationService")
        self.ocr_processor = DocumentOCRProcessor()
        self.face_service = FaceVerificationService()
        logger.info("VerificationService initialized successfully")

    async def verify_document(self, document_image: bytes) -> VerificationResult:
        """
        Process and verify uploaded ID document
        - Extracts information using Claude OCR
        - Stores document in S3
        """
        logger.info("Starting document verification process")
        try:
            # Extract information using Claude
            logger.info("Extracting information from document using OCR")
            doc_result = await self.ocr_processor.process_document(document_image)

            if not doc_result.document_info:
                logger.warning("Failed to extract information from document")
                return VerificationResult(
                    success=False,
                    stage="document_verification",
                    message="Failed to extract information from document",
                )

            # Generate unique ID for document storage
            doc_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Store document in S3
            s3_key = f"documents/{doc_id}_{timestamp}.jpg"
            logger.info(f"Storing document in S3 with key: {s3_key}")
            s3_path = await self.face_service.upload_to_s3(document_image, s3_key)

            logger.success("Document verification completed successfully")
            return VerificationResult(
                success=True,
                stage="document_verification",
                message="Document processed successfully",
                details={
                    "extracted_info": doc_result.document_info.dict(),
                    "image_path": s3_key,
                },
            )

        except Exception as e:
            error_msg = f"Document verification failed: {str(e)}"
            logger.error(error_msg)
            return VerificationResult(
                success=False, stage="document_verification", message=error_msg
            )

    async def verify_biometrics(
        self, selfie_image: bytes, id_photo_path: str
    ) -> VerificationResult:
        """
        Verify user's biometric information
        - Compares selfie with ID photo
        """
        logger.info("Starting biometric verification process")
        try:
            # Generate unique ID for selfie storage
            selfie_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Store selfie in S3
            s3_key = f"selfies/{selfie_id}_{timestamp}.jpg"
            logger.info(f"Storing selfie in S3 with key: {s3_key}")
            s3_path = await self.face_service.upload_to_s3(selfie_image, s3_key)

            # Compare faces
            logger.info("Comparing faces")
            match_found, similarity = await self.face_service.compare_faces(
                source_image_key=id_photo_path, target_image_key=s3_key
            )

            if not match_found:
                logger.warning(
                    f"Face comparison failed with similarity score: {similarity}"
                )
                return VerificationResult(
                    success=False,
                    stage="biometric_verification",
                    message="Face comparison failed - faces don't match",
                    details={"similarity_score": similarity},
                )

            logger.success("Biometric verification completed successfully")
            return VerificationResult(
                success=True,
                stage="biometric_verification",
                message="Biometric verification successful",
                details={"selfie_path": s3_key, "face_match_score": similarity},
            )

        except Exception as e:
            error_msg = f"Biometric verification failed: {str(e)}"
            logger.error(error_msg)
            return VerificationResult(
                success=False, stage="biometric_verification", message=error_msg
            )

    async def complete_verification(
        self, session: Dict, customer_data: CustomerCreateRequest
    ) -> VerificationResult:
        """
        Complete full verification process and create customer record
        """
        logger.info("Starting verification completion process")
        try:
            # Create customer record
            logger.info("Creating customer record")
            customer = Customer(
                **customer_data.dict(),
                document_image_path=session["document_image_path"],
                selfie_image_path=session["selfie_path"],
                verification_status="verified",
                verification_date=datetime.now(),
            )

            # Save to database (implementation depends on your DB setup)
            # await self.db.save(customer)
            logger.info(f"Customer record created with ID: {customer.id}")

            logger.success("Verification completion process successful")
            return VerificationResult(
                success=True,
                stage="registration",
                message="Customer registration completed",
                details={"customer_id": str(customer.id)},
            )

        except Exception as e:
            error_msg = f"Registration failed: {str(e)}"
            logger.error(error_msg)
            return VerificationResult(
                success=False, stage="registration", message=error_msg
            )
