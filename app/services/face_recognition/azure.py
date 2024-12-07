from azure.cognitiveservices.vision.face import FaceClient
from azure.cognitiveservices.vision.face.models import APIErrorException
from msrest.authentication import CognitiveServicesCredentials
from app.core.config import settings
import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class AzureFaceService:
    def __init__(self):
        self.endpoint = settings.AZURE_FACE_ENDPOINT
        self.key = settings.AZURE_FACE_KEY
        self.face_client = FaceClient(
            self.endpoint,
            CognitiveServicesCredentials(self.key)
        )
        self.confidence_threshold = 0.6  # Configurable confidence threshold for face matching

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                'Ocp-Apim-Subscription-Key': self.key,
                'Content-Type': 'application/octet-stream'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def detect_face(self, image_data: bytes) -> Dict[str, Any]:
        """
        Detect face in an image and return face attributes
        """
        try:
            url = f"{self.endpoint}/face/v1.0/detect"
            params = {
                'returnFaceId': 'true',
                'returnFaceLandmarks': 'false',
                'returnFaceAttributes': 'age,gender,headPose,smile,facialHair,glasses,emotion,makeup'
            }

            async with self.session.post(url, params=params, data=image_data) as response:
                result = await response.json()
                
                if not result:
                    logger.warning("No face detected in the image")
                    return {}
                    
                face_data = result[0]  # Get the first face
                logger.info(f"Face detected with ID: {face_data.get('faceId')}")
                return face_data
                
        except Exception as e:
            logger.error(f"Face detection error: {str(e)}")
            raise

    async def verify_liveness(self, video_data: bytes, face_id: str) -> Dict[str, Any]:
        """
        Verify liveness from video stream
        """
        try:
            url = f"{self.endpoint}/face/v1.0/verify_liveness"
            params = {
                'faceId': face_id
            }

            async with self.session.post(url, params=params, data=video_data) as response:
                result = await response.json()
                logger.info(f"Liveness check completed with result: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Liveness verification error: {str(e)}")
            raise

    async def compare_faces(self, face_id1: str, face_id2: str) -> Dict[str, Any]:
        """
        Compare two faces and return similarity score
        """
        try:
            url = f"{self.endpoint}/face/v1.0/verify"
            data = {
                'faceId1': face_id1,
                'faceId2': face_id2
            }

            async with self.session.post(url, json=data) as response:
                result = await response.json()
                
                is_match = result.get('isIdentical', False) or (
                    result.get('confidence', 0) >= self.confidence_threshold
                )
                
                comparison_result = {
                    'isMatch': is_match,
                    'confidence': result.get('confidence', 0),
                    'success': True,
                    'message': 'Face comparison completed successfully'
                }
                
                logger.info(
                    f"Face comparison completed. Match: {is_match}, "
                    f"Confidence: {result.get('confidence', 0)}"
                )
                
                return comparison_result
                
        except Exception as e:
            logger.error(f"Face comparison error: {str(e)}")
            return {
                'isMatch': False,
                'confidence': 0,
                'success': False,
                'message': f"Face comparison failed: {str(e)}"
            }

    async def extract_face_from_document(self, document_image: bytes) -> Optional[Dict[str, Any]]:
        """
        Extract face from ID document image
        """
        try:
            url = f"{self.endpoint}/face/v1.0/detect"
            params = {
                'returnFaceId': 'true',
                'returnFaceLandmarks': 'false',
                'returnFaceAttributes': 'age,gender'
            }

            async with self.session.post(url, params=params, data=document_image) as response:
                result = await response.json()
                
                if not result:
                    logger.warning("No face detected in the document image")
                    return None
                    
                # Get the largest face in the document (usually the ID photo)
                faces = sorted(
                    result,
                    key=lambda x: (
                        x.get('faceRectangle', {}).get('width', 0) *
                        x.get('faceRectangle', {}).get('height', 0)
                    ),
                    reverse=True
                )
                
                document_face = faces[0]
                logger.info(f"Face extracted from document with ID: {document_face.get('faceId')}")
                return document_face
                
        except Exception as e:
            logger.error(f"Document face extraction error: {str(e)}")
            return None

    async def verify_face_match(
        self,
        selfie_image: bytes,
        document_image: bytes
    ) -> Dict[str, Any]:
        """
        Complete face verification process:
        1. Detect face in selfie
        2. Extract face from document
        3. Compare faces
        """
        try:
            # Detect face in selfie
            selfie_face = await self.detect_face(selfie_image)
            if not selfie_face:
                return {
                    'success': False,
                    'message': 'No face detected in selfie image'
                }

            # Extract face from document
            document_face = await self.extract_face_from_document(document_image)
            if not document_face:
                return {
                    'success': False,
                    'message': 'No face detected in document image'
                }

            # Compare faces
            comparison_result = await self.compare_faces(
                selfie_face['faceId'],
                document_face['faceId']
            )

            return {
                'success': comparison_result['isMatch'],
                'confidence': comparison_result['confidence'],
                'selfie_face_id': selfie_face['faceId'],
                'document_face_id': document_face['faceId'],
                'message': (
                    'Face verification successful'
                    if comparison_result['isMatch']
                    else 'Face verification failed: faces do not match'
                ),
                'face_match': comparison_result['isMatch'],
                'face_match_score': comparison_result['confidence']
            }

        except Exception as e:
            logger.error(f"Face verification error: {str(e)}")
            return {
                'success': False,
                'message': f"Face verification failed: {str(e)}"
            }