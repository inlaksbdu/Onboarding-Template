import boto3
from typing import Dict, Optional, Tuple
from botocore.exceptions import ClientError
from Library.config import settings
from loguru import logger

class FaceVerificationService:
    def __init__(self):
        """Initialize AWS Rekognition client"""
        logger.info("Initializing FaceVerificationService")
        try:
            self.rekognition = boto3.client(
                'rekognition',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            self.bucket_name = settings.aws_bucket_name
            logger.info("Successfully initialized AWS clients")
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            raise

    async def upload_to_s3(self, image_bytes: bytes, key: str) -> str:
        """
        Upload image to S3 bucket
        
        Args:
            image_bytes: Image data in bytes
            key: S3 object key (path/filename)
            
        Returns:
            str: S3 URI of uploaded image
        """
        logger.info(f"Uploading image to S3 with key: {key}")
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image_bytes,
                ContentType='image/jpeg'
            )
            s3_uri = f"s3://{self.bucket_name}/{key}"
            logger.success(f"Successfully uploaded image to {s3_uri}")
            return s3_uri
        except ClientError as e:
            error_msg = f"Failed to upload image to S3: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def verify_face_quality(self, image_bytes: bytes) -> Tuple[bool, Dict]:
        """
        Verify face quality using AWS Rekognition DetectFaces
        
        Args:
            image_bytes: Image data in bytes
            
        Returns:
            Tuple[bool, Dict]: (is_valid, details)
        """
        logger.info("Verifying face quality")
        try:
            response = self.rekognition.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['ALL']
            )

            if not response['FaceDetails']:
                logger.warning("No face detected in the image")
                return False, {
                    "error": "No face detected in the image",
                    "suggestions": ["Please ensure your face is clearly visible in the image"]
                }

            face_detail = response['FaceDetails'][0]
            
            # Enhanced quality checks
            checks = {
                "is_face_detected": True,
                "is_human": face_detail.get('Confidence', 0) > 95,  # High confidence threshold for human face
                "face_occluded": any([
                    face_detail.get('Occlusions', []).get('EyesOccluded', {}).get('Value', False),
                    face_detail.get('Occlusions', []).get('MouthOccluded', {}).get('Value', False),
                    face_detail.get('Occlusions', []).get('NoseOccluded', {}).get('Value', False)
                ]),
                "pose_valid": all([
                    abs(face_detail.get('Pose', {}).get('Pitch', 0)) < 20,  # Face looking straight ahead
                    abs(face_detail.get('Pose', {}).get('Roll', 0)) < 20,   # Head not tilted
                    abs(face_detail.get('Pose', {}).get('Yaw', 0)) < 20     # Face not turned sideways
                ]),
                "eyes_open": face_detail.get('EyesOpen', {}).get('Value', True),
                "quality_brightness": face_detail.get('Quality', {}).get('Brightness', 0) > 50,
                "quality_sharpness": face_detail.get('Quality', {}).get('Sharpness', 0) > 50,
                "sunglasses": not face_detail.get('Sunglasses', {}).get('Value', False),
                "mouth_open": not face_detail.get('MouthOpen', {}).get('Value', False),
                "multiple_faces": len(response['FaceDetails']) == 1  # Only one face should be present
            }
            
            is_valid = all(checks.values())
            
            logger.info(f"Face quality verification complete: is_valid={is_valid}")
            logger.debug(f"Quality check details: {checks}")
            
            return is_valid, {
                "checks": checks,
                "suggestions": self._generate_suggestions(checks)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = str(e)
            logger.error(f"AWS Rekognition DetectFaces failed: {error_msg}")
            
            if error_code == 'InvalidImageFormatException':
                return False, {
                    "error": "Invalid image format",
                    "suggestions": ["Please provide a valid JPEG or PNG image"]
                }
            elif error_code == 'InvalidParameterException':
                return False, {
                    "error": "Invalid image",
                    "suggestions": ["Please provide a clear photo with your face visible"]
                }
            elif error_code == 'ImageTooLargeException':
                return False, {
                    "error": "Image too large",
                    "suggestions": ["Please provide an image smaller than 5MB"]
                }
            else:
                raise Exception(f"Face detection failed: {error_msg}")

    def _generate_suggestions(self, checks: Dict[str, bool]) -> list:
        """Generate user-friendly suggestions based on failed checks"""
        logger.info("Generating suggestions")
        suggestions = []
        
        if not checks["is_face_detected"]:
            suggestions.append("Please ensure your face is clearly visible in the image")
        if not checks["is_human"]:
            suggestions.append("Please provide a clear photo of a human face")
        if checks["face_occluded"]:
            suggestions.append("Please remove any objects blocking your face (hands, mask, etc.)")
        if not checks["pose_valid"]:
            suggestions.append("Please look straight at the camera without tilting or turning your head")
        if not checks["eyes_open"]:
            suggestions.append("Please open your eyes for the photo")
        if not checks["quality_brightness"]:
            suggestions.append("Please take the photo in better lighting")
        if not checks["quality_sharpness"]:
            suggestions.append("Please hold the camera steady and ensure the image is clear")
        if not checks["sunglasses"]:
            suggestions.append("Please remove sunglasses or any eye accessories")
        if checks["mouth_open"]:
            suggestions.append("Please close your mouth for the photo")
        if not checks["multiple_faces"]:
            suggestions.append("Please ensure only your face is visible in the photo")
            
        logger.info(f"Generated {len(suggestions)} suggestions")
        return suggestions

    async def compare_faces(
        self,
        source_image_key: str,
        target_image_key: str,
        similarity_threshold: float = 90
    ) -> Tuple[bool, float]:
        """
        Compare faces between source (ID card) and target (selfie) images
        
        Args:
            source_image_key: S3 key for source image (ID card)
            target_image_key: S3 key for target image (selfie)
            similarity_threshold: Minimum similarity threshold (0-100)
            
        Returns:
            Tuple[bool, float]: (match_found, similarity_score)
        """
        logger.info(
            f"Comparing faces: source={source_image_key}, target={target_image_key}, "
            f"threshold={similarity_threshold}"
        )
        
        try:
            response = self.rekognition.compare_faces(
                SourceImage={
                    'S3Object': {
                        'Bucket': self.bucket_name,
                        'Name': source_image_key
                    }
                },
                TargetImage={
                    'S3Object': {
                        'Bucket': self.bucket_name,
                        'Name': target_image_key
                    }
                },
                SimilarityThreshold=similarity_threshold,
                QualityFilter='HIGH'  # Ensure high-quality face detection
            )
            
            if not response.get('FaceMatches'):
                logger.warning("No matching faces found")
                return False, 0.0
                
            # Get the highest similarity score
            best_match = max(response['FaceMatches'], key=lambda x: x['Similarity'])
            similarity = best_match['Similarity']
            
            match_found = similarity >= similarity_threshold
            logger.info(f"Face comparison complete: match_found={match_found}, similarity={similarity:.2f}%")
            
            return match_found, similarity
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = str(e)
            logger.error(f"AWS Rekognition CompareFaces failed: {error_msg}")
            
            if error_code == 'InvalidParameterException':
                logger.warning("Face comparison failed due to invalid parameters - likely no face detected")
                return False, 0.0
            elif error_code == 'InvalidS3ObjectException':
                raise Exception("One or both images not found in S3")
            elif error_code == 'ImageTooLargeException':
                raise Exception("One or both images exceed the size limit (5MB)")
            elif error_code == 'InvalidImageFormatException':
                raise Exception("One or both images are in an invalid format (must be JPG or PNG)")
            else:
                raise Exception(f"Face comparison failed: {error_msg}")
