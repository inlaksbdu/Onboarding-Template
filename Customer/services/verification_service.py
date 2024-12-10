from typing import Optional, Dict, List
import os
import io
import boto3
from azure.cognitiveservices.vision.face import FaceClient
from azure.cognitiveservices.vision.face.models import VerifyResult, DetectedFace
from msrest.authentication import CognitiveServicesCredentials
from fastapi import HTTPException
from pydantic import BaseModel
from loguru import logger

from Library.utils import DocumentOCRProcessor, DocumentExtractionResult

class VerificationResult(BaseModel):
    success: bool
    stage: str
    message: str
    details: Optional[Dict] = None

class BiometricVerificationResult(BaseModel):
    liveness_score: float
    face_match_score: float
    liveness_verified: bool
    face_match_verified: bool
    details: Optional[Dict] = None

class VerificationService:
    def __init__(self):
        self.ocr_processor = DocumentOCRProcessor()
        
        # Initialize AWS Rekognition
        self.rekognition = boto3.client('rekognition',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        
        # Initialize Azure Face Client
        self.face_client = FaceClient(
            os.getenv('AZURE_FACE_ENDPOINT'),
            CognitiveServicesCredentials(os.getenv('AZURE_FACE_KEY'))
        )

    async def verify_document(self, document_image: bytes) -> VerificationResult:
        """Process and verify uploaded ID document"""
        try:
            # 1. Extract information using Claude OCR
            doc_info = await self.ocr_processor.process_document(document_image)
            
            # 2. Verify with National ID Database
            # TODO: Implement national ID verification
            
            # 3. Perform AML Check
            # TODO: Implement AML check
            
            # 4. Perform Credit Bureau Check
            # TODO: Implement credit check
            
            return VerificationResult(
                success=True,
                stage="document_verification",
                message="Document verified successfully",
                details=doc_info.dict()
            )
        except Exception as e:
            logger.error(f"Document verification failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def verify_biometrics(self, selfie_image: bytes, id_photo: bytes) -> BiometricVerificationResult:
        """Verify user's biometric information using Azure for liveness and AWS for face comparison"""
        try:
            # Convert bytes to stream for Azure Face API
            selfie_stream = io.BytesIO(selfie_image)
            
            # 1. Azure Liveness Detection
            detected_faces = self.face_client.face.detect_with_stream(
                image=selfie_stream,
                return_face_attributes=['headPose', 'blur', 'exposure', 'noise'],
                detection_model='detection_01'
            )
            
            if not detected_faces:
                return BiometricVerificationResult(
                    liveness_score=0.0,
                    face_match_score=0.0,
                    liveness_verified=False,
                    face_match_verified=False,
                    details={"error": "No face detected in selfie"}
                )
            
            # Analyze face attributes for liveness
            face_attributes = detected_faces[0].face_attributes
            blur_score = 1 - face_attributes.blur.value
            exposure_score = 1 - abs(0.5 - face_attributes.exposure.value)
            quality_score = (blur_score + exposure_score) / 2
            
            # 2. AWS Rekognition Face Comparison
            comparison_response = self.rekognition.compare_faces(
                SourceImage={'Bytes': id_photo},
                TargetImage={'Bytes': selfie_image},
                SimilarityThreshold=90
            )
            
            if not comparison_response['FaceMatches']:
                return BiometricVerificationResult(
                    liveness_score=quality_score * 100,
                    face_match_score=0.0,
                    liveness_verified=quality_score >= 0.8,
                    face_match_verified=False,
                    details={"error": "No matching faces found"}
                )
            
            similarity = comparison_response['FaceMatches'][0]['Similarity']
            
            return BiometricVerificationResult(
                liveness_score=quality_score * 100,
                face_match_score=similarity,
                liveness_verified=quality_score >= 0.8,
                face_match_verified=similarity >= 90,
                details={
                    "blur_score": blur_score,
                    "exposure_score": exposure_score,
                    "similarity_score": similarity
                }
            )
            
        except Exception as e:
            logger.error(f"Biometric verification failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def complete_verification(self, 
                                 document_image: bytes,
                                 selfie_image: bytes) -> Dict[str, VerificationResult]:
        """Complete full verification process"""
        results = {}
        
        # 1. Document Verification
        results['document'] = await self.verify_document(document_image)
        if not results['document'].success:
            return results
            
        # 2. Extract photo from ID for comparison
        # TODO: Implement ID photo extraction
        id_photo = document_image  # Placeholder
        
        # 3. Biometric Verification
        results['biometric'] = await self.verify_biometrics(selfie_image, id_photo)
        
        return results
