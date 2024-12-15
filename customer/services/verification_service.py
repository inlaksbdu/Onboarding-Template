import asyncio
from typing import Optional, Dict, List
import uuid
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from ocr.extractor import DocumentOCRProcessor
from customer.services.face_verification_service import FaceVerificationService
from customer.dto.requests.customer_request import CustomerCreateRequest
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
    def __init__(
        self, ocr_processor: DocumentOCRProcessor, face_service: FaceVerificationService
    ):
        self.ocr_processor = ocr_processor
        self.face_service = face_service

    async def verify_document(self, document_images: List) -> VerificationResult:
        """
        Process and verify uploaded ID document
        - Extracts information using Claude OCR
        - Stores document in S3
        """
        try:
            doc_result = await self.ocr_processor.process_images(document_images)

            s3_paths = await asyncio.gather(
                *(
                    self.face_service.upload_to_s3(document_image)
                    for document_image in document_images
                )
            )

            logger.success("Document verification completed successfully")
            return VerificationResult(
                success=True,
                stage="document_verification",
                message="Document processed successfully",
                details={
                    "extracted_info": doc_result.model_dump(),
                    "images_path": s3_paths,
                },
            )

        except Exception as e:
            error_msg = f"Document verification failed: {str(e)}"
            logger.error(error_msg)
            return VerificationResult(
                success=False, stage="document_verification", message=error_msg
            )

    async def compare_faces(
        self, selfie_image: bytes, id_photo_path: str, threshold: float = 90
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
                source_image_key=id_photo_path,
                target_image_key=s3_key,
                similarity_threshold=threshold,
            )

            if not match_found or similarity < threshold:
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
