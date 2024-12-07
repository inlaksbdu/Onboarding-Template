from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from app.core.config import settings
import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.endpoint = settings.AZURE_VISION_ENDPOINT
        self.key = settings.AZURE_VISION_KEY
        self.vision_client = ComputerVisionClient(
            self.endpoint,
            CognitiveServicesCredentials(self.key)
        )

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

    async def extract_data(self, image_data: bytes, document_type: str) -> Dict[str, Any]:
        """
        Extract text and data from document images using Azure's OCR
        """
        try:
            # Start the OCR operation
            url = f"{self.endpoint}/vision/v3.2/read/analyze"
            async with self.session.post(url, data=image_data) as response:
                if response.status != 202:
                    raise Exception(f"OCR operation failed: {response.status}")
                
                # Get the operation location for polling
                operation_location = response.headers["Operation-Location"]
                operation_id = operation_location.split("/")[-1]

            # Poll for results
            max_retries = 10
            retry_delay = 1
            for _ in range(max_retries):
                async with self.session.get(operation_location) as response:
                    result = await response.json()
                    
                    if result.get("status") == OperationStatusCodes.succeeded.value:
                        # Process the results based on document type
                        extracted_data = await self._process_ocr_result(
                            result.get("analyzeResult", {}),
                            document_type
                        )
                        
                        logger.info(f"OCR completed successfully for document type: {document_type}")
                        return extracted_data
                        
                    elif result.get("status") == OperationStatusCodes.failed.value:
                        raise Exception(f"OCR operation failed: {result.get('error', {}).get('message')}")
                        
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

            raise Exception("OCR operation timed out")

        except Exception as e:
            logger.error(f"OCR extraction error: {str(e)}")
            raise

    async def _process_ocr_result(
        self,
        ocr_result: Dict[str, Any],
        document_type: str
    ) -> Dict[str, Any]:
        """
        Process OCR results based on document type
        """
        try:
            # Extract all text lines
            text_lines = []
            for read_result in ocr_result.get("readResults", []):
                for line in read_result.get("lines", []):
                    text_lines.append(line.get("text", ""))

            # Process based on document type
            extracted_data = {
                "raw_text": "\n".join(text_lines),
                "document_type": document_type,
                "extraction_time": datetime.utcnow().isoformat(),
            }

            # Extract specific fields based on document type
            if document_type == "PASSPORT":
                extracted_data.update(self._extract_passport_data(text_lines))
            elif document_type == "NATIONAL_ID":
                extracted_data.update(self._extract_national_id_data(text_lines))
            elif document_type == "DRIVING_LICENSE":
                extracted_data.update(self._extract_driving_license_data(text_lines))

            return extracted_data

        except Exception as e:
            logger.error(f"OCR result processing error: {str(e)}")
            raise

    def _extract_passport_data(self, text_lines: list) -> Dict[str, Any]:
        """Extract data from passport"""
        data = {
            "document_number": None,
            "surname": None,
            "given_names": None,
            "date_of_birth": None,
            "expiry_date": None,
            "nationality": None,
            "gender": None
        }
        
        # Process each line to find relevant information
        for line in text_lines:
            # Look for MRZ lines (usually last 2-3 lines)
            if len(line) == 44 and line[0] == "P":  # Passport MRZ first line
                data["document_number"] = line[5:14].strip("<")
                data["nationality"] = line[2:5]
            
            # Look for other fields
            lower_line = line.lower()
            if "surname" in lower_line or "last name" in lower_line:
                data["surname"] = self._extract_field_value(line)
            elif "given names" in lower_line or "first name" in lower_line:
                data["given_names"] = self._extract_field_value(line)
            elif "birth" in lower_line or "dob" in lower_line:
                data["date_of_birth"] = self._extract_date(line)
            elif "expiry" in lower_line or "exp" in lower_line:
                data["expiry_date"] = self._extract_date(line)
            elif "gender" in lower_line or "sex" in lower_line:
                data["gender"] = self._extract_gender(line)

        return data

    def _extract_national_id_data(self, text_lines: list) -> Dict[str, Any]:
        """Extract data from national ID"""
        data = {
            "id_number": None,
            "full_name": None,
            "date_of_birth": None,
            "address": None,
            "gender": None
        }
        
        address_lines = []
        for line in text_lines:
            lower_line = line.lower()
            if "id" in lower_line and any(c.isdigit() for c in line):
                data["id_number"] = self._extract_field_value(line)
            elif "name" in lower_line:
                data["full_name"] = self._extract_field_value(line)
            elif "birth" in lower_line or "dob" in lower_line:
                data["date_of_birth"] = self._extract_date(line)
            elif "gender" in lower_line or "sex" in lower_line:
                data["gender"] = self._extract_gender(line)
            elif "address" in lower_line:
                start_collecting = True
            elif start_collecting and line.strip():
                address_lines.append(line.strip())

        if address_lines:
            data["address"] = " ".join(address_lines)

        return data

    def _extract_driving_license_data(self, text_lines: list) -> Dict[str, Any]:
        """Extract data from driving license"""
        data = {
            "license_number": None,
            "full_name": None,
            "date_of_birth": None,
            "address": None,
            "license_class": None,
            "expiry_date": None
        }
        
        address_lines = []
        for line in text_lines:
            lower_line = line.lower()
            if "license" in lower_line and any(c.isdigit() for c in line):
                data["license_number"] = self._extract_field_value(line)
            elif "name" in lower_line:
                data["full_name"] = self._extract_field_value(line)
            elif "birth" in lower_line or "dob" in lower_line:
                data["date_of_birth"] = self._extract_date(line)
            elif "class" in lower_line:
                data["license_class"] = self._extract_field_value(line)
            elif "expiry" in lower_line or "exp" in lower_line:
                data["expiry_date"] = self._extract_date(line)
            elif "address" in lower_line:
                start_collecting = True
            elif start_collecting and line.strip():
                address_lines.append(line.strip())

        if address_lines:
            data["address"] = " ".join(address_lines)

        return data

    def _extract_field_value(self, line: str) -> Optional[str]:
        """Extract value after colon or similar separator"""
        separators = [':', '-', '=']
        for sep in separators:
            if sep in line:
                return line.split(sep)[1].strip()
        return line.strip()

    def _extract_date(self, line: str) -> Optional[str]:
        """Extract and standardize date from text"""
        # Implementation would include date parsing logic
        # This is a placeholder - would need proper date parsing
        return self._extract_field_value(line)

    def _extract_gender(self, line: str) -> Optional[str]:
        """Extract and standardize gender"""
        value = self._extract_field_value(line).upper()
        if 'F' in value or 'FEMALE' in value:
            return 'F'
        elif 'M' in value or 'MALE' in value:
            return 'M'
        return None
