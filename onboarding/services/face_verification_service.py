from datetime import datetime
import uuid
import boto3
from typing import Dict, Optional, Tuple
from botocore.exceptions import ClientError
from library.config import settings
from loguru import logger


class FaceVerificationService:
    def __init__(self):
        """Initialize AWS Rekognition client"""
        try:
            self.rekognition = boto3.client(
                "rekognition",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
            )
            self.s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
            )
            self.bucket_name = settings.aws_bucket_name
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            raise

    @staticmethod
    def generate_doc_id() -> str:
        doc_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_key = f"documents/{doc_id}_{timestamp}.jpg"
        return s3_key
    

    async def check_image_quality(self, image_bytes: bytes) -> Dict:
        """
        Check image quality using AWS Rekognition DetectModerationLabels

        Args:
            image_bytes: Image data in bytes

        Returns:
            Dict: Quality check results
        """
        logger.info("Starting image quality check")
        try:
            response = self.rekognition.detect_moderation_labels(
                Image={"Bytes": image_bytes}
            )

            is_human = False
            is_face_detected = False
            face_occluded = False
            pose_valid = False
            eyes_open = False
            quality_brightness = False
            quality_sharpness = False
            sunglasses = False
            mouth_open = False
            multiple_faces = False

            for label in response.get("ModerationLabels", []):
                if label["Name"] == "Human":
                    is_human = True
                if label["Name"] == "Face":
                    is_face_detected = True
                if label["Name"] == "Sunglasses":
                    sunglasses = True
                if label["Name"] == "EyesOpen":
                    eyes_open = True
                if label["Name"] == "MouthOpen":
                    mouth_open = True
                if label["Name"] == "FaceOccluded":
                    face_occluded = True
                if label["Name"] == "Pose":
                    pose_valid = True
                if label["Name"] == "Apparel":
                    if label["Confidence"] > 90:
                        multiple_faces = True

            # Image quality checks
            brightness = response.get("ImageQuality", {}).get("Brightness", 0)
            sharpness = response.get("ImageQuality", {}).get("Sharpness", 0)

            quality_brightness = brightness > 50
            quality_sharpness = sharpness > 50

            logger.info("Image quality check complete")
            return {
                "is_human": is_human,
                "is_face_detected": is_face_detected,
                "face_occluded": face_occluded,
                "pose_valid": pose_valid,
                "eyes_open": eyes_open,
                "quality_brightness": quality_brightness,
                "quality_sharpness": quality_sharpness,
                "sunglasses": sunglasses,
                "mouth_open": mouth_open,
                "multiple_faces": multiple_faces,
            }

        except ClientError as e:
            error_msg = f"Failed to check image quality: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def upload_to_s3(self, image_bytes: bytes, key: str | None = None) -> str:
        """
        Upload image to S3 bucket

        Args:
            image_bytes: Image data in bytes
            key: S3 object key (path/filename)

        Returns:
            str: S3 URI of uploaded image
        """
        key = key or self.generate_doc_id()
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image_bytes,
                ContentType="image/jpeg",
            )
            s3_uri = f"s3://{self.bucket_name}/{key}"
            return key
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
        logger.info("Starting face quality verification")
        try:
            # Request specific attributes we want to check
            response = self.rekognition.detect_faces(
                Image={"Bytes": image_bytes},
                Attributes=[
                    "DEFAULT",  # Includes BoundingBox, Confidence, Pose, Quality, and Landmarks
                    "AGE_RANGE",
                    "SUNGLASSES",
                    "EYES_OPEN",
                    "MOUTH_OPEN",
                    "FACE_OCCLUDED",
                ],
            )

            if not response.get("FaceDetails"):
                logger.warning("No face detected in the image")
                return False, {
                    "error": "No face detected",
                    "suggestions": [
                        "Please ensure your face is clearly visible in the image"
                    ],
                }

            # Get the first (and should be only) face
            face = response["FaceDetails"][0]

            # Initialize quality checks dictionary
            quality_checks = {}
            suggestions = []

            # 1. Check Face Detection Confidence
            quality_checks["face_confidence"] = face.get("Confidence", 0) > 90
            if not quality_checks["face_confidence"]:
                suggestions.append("Please provide a clearer photo of your face")

            # 2. Age Range Check (store for reference)
            age_range = face.get("AgeRange", {})
            quality_checks["age_range"] = {
                "low": age_range.get("Low", 0),
                "high": age_range.get("High", 0),
            }

            # 3. Sunglasses Check
            sunglasses = face.get("Sunglasses", {})
            quality_checks["sunglasses"] = not sunglasses.get("Value", False)
            if not quality_checks["sunglasses"]:
                suggestions.append("Please remove sunglasses")

            # 4. Eyes Open Check
            eyes_open = face.get("EyesOpen", {})
            quality_checks["eyes_open"] = eyes_open.get("Value", True)
            if not quality_checks["eyes_open"]:
                suggestions.append("Please open your eyes fully")

            # 5. Mouth Open Check
            mouth_open = face.get("MouthOpen", {})
            quality_checks["mouth_closed"] = not mouth_open.get("Value", False)
            if not quality_checks["mouth_closed"]:
                suggestions.append("Please close your mouth")

            # 6. Face Occlusion Check
            face_occluded = face.get("FaceOccluded", {})
            quality_checks["face_clear"] = not face_occluded.get("Value", False)
            if not quality_checks["face_clear"]:
                suggestions.append("Please remove any objects blocking your face")

            # 7. Image Quality Checks
            quality = face.get("Quality", {})
            brightness = quality.get("Brightness", 0)
            sharpness = quality.get("Sharpness", 0)

            quality_checks["brightness"] = brightness > 50
            quality_checks["sharpness"] = sharpness > 50

            if not quality_checks["brightness"]:
                suggestions.append("Please take the photo in better lighting")
            if not quality_checks["sharpness"]:
                suggestions.append("Please ensure the image is clear and not blurry")

            # 8. Face Pose Check (ensure face is looking straight ahead)
            pose = face.get("Pose", {})
            pose_threshold = 20  # degrees
            quality_checks["pose_valid"] = all(
                [
                    abs(pose.get("Pitch", 0)) < pose_threshold,
                    abs(pose.get("Roll", 0)) < pose_threshold,
                    abs(pose.get("Yaw", 0)) < pose_threshold,
                ]
            )
            if not quality_checks["pose_valid"]:
                suggestions.append("Please look straight at the camera")

            # Overall validation
            required_checks = [
                "face_confidence",
                "sunglasses",
                "eyes_open",
                "mouth_closed",
                "face_clear",
                "brightness",
                "sharpness",
                "pose_valid",
            ]

            is_valid = all(
                quality_checks.get(check, False) for check in required_checks
            )

            logger.info(f"Face quality verification complete: is_valid={is_valid}")
            logger.debug(f"Quality check details: {quality_checks}")

            return is_valid, {
                "checks": quality_checks,
                "suggestions": suggestions,
                "age_range": quality_checks["age_range"],
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = str(e)
            logger.error(f"AWS Rekognition DetectFaces failed: {error_msg}")

            error_mapping = {
                "InvalidImageFormatException": {
                    "error": "Invalid image format",
                    "suggestions": ["Please provide a valid JPEG or PNG image"],
                },
                "ImageTooLargeException": {
                    "error": "Image too large",
                    "suggestions": ["Please provide an image smaller than 5MB"],
                },
                "InvalidParameterException": {
                    "error": "Invalid image",
                    "suggestions": [
                        "Please provide a clear photo with your face visible"
                    ],
                },
                "AccessDeniedException": {
                    "error": "Access denied",
                    "suggestions": ["Please check your AWS credentials"],
                },
                "ProvisionedThroughputExceededException": {
                    "error": "Too many requests",
                    "suggestions": ["Please try again in a few moments"],
                },
                "ThrottlingException": {
                    "error": "Service throttled",
                    "suggestions": ["Please try again in a few moments"],
                },
            }

            if error_code in error_mapping:
                return False, error_mapping[error_code]
            else:
                raise Exception(f"Face detection failed: {error_msg}")

    async def compare_faces(
        self,
        source_image_key: str,
        target_image_key: str,
        similarity_threshold: float = 90,
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
                    "S3Object": {"Bucket": self.bucket_name, "Name": source_image_key}
                },
                TargetImage={
                    "S3Object": {"Bucket": self.bucket_name, "Name": target_image_key}
                },
                SimilarityThreshold=similarity_threshold,
                QualityFilter="HIGH",  # Ensure high-quality face detection
            )

            if not response.get("FaceMatches"):
                logger.warning("No matching faces found")
                return False, 0.0

            # Get the highest similarity score
            best_match = max(response["FaceMatches"], key=lambda x: x["Similarity"])
            similarity = best_match["Similarity"]

            match_found = similarity >= similarity_threshold
            logger.info(
                f"Face comparison complete: match_found={match_found}, similarity={similarity:.2f}%"
            )

            return match_found, similarity

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = str(e)
            logger.error(f"AWS Rekognition CompareFaces failed: {error_msg}")

            if error_code == "InvalidParameterException":
                logger.warning(
                    "Face comparison failed due to invalid parameters - likely no face detected"
                )
                return False, 0.0
            elif error_code == "InvalidS3ObjectException":
                raise Exception("One or both images not found in S3")
            elif error_code == "ImageTooLargeException":
                raise Exception("One or both images exceed the size limit (5MB)")
            elif error_code == "InvalidImageFormatException":
                raise Exception(
                    "One or both images are in an invalid format (must be JPG or PNG)"
                )
            else:
                raise Exception(f"Face comparison failed: {error_msg}")

    def _generate_suggestions(self, checks: Dict[str, bool]) -> list:
        """Generate user-friendly suggestions based on failed checks"""
        logger.info("Generating suggestions")
        suggestions = []

        if not checks["is_face_detected"]:
            suggestions.append(
                "Please ensure your face is clearly visible in the image"
            )
        if not checks["is_human"]:
            suggestions.append("Please provide a clear photo of a human face")
        if checks["face_occluded"]:
            suggestions.append(
                "Please remove any objects blocking your face (hands, mask, etc.)"
            )
        if not checks["pose_valid"]:
            suggestions.append(
                "Please look straight at the camera without tilting or turning your head"
            )
        if not checks["eyes_open"]:
            suggestions.append("Please open your eyes for the photo")
        if not checks["quality_brightness"]:
            suggestions.append("Please take the photo in better lighting")
        if not checks["quality_sharpness"]:
            suggestions.append(
                "Please hold the camera steady and ensure the image is clear"
            )
        if not checks["sunglasses"]:
            suggestions.append("Please remove sunglasses or any eye accessories")
        if checks["mouth_open"]:
            suggestions.append("Please close your mouth for the photo")
        if not checks["multiple_faces"]:
            suggestions.append("Please ensure only your face is visible in the photo")

        logger.info(f"Generated {len(suggestions)} suggestions")
        return suggestions
