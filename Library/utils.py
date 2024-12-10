import base64
import asyncio
from typing import List, Optional, Dict, Union
from pydantic import BaseModel, Field
from Library.config import settings
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
import os

class DocumentExtractionResult(BaseModel):
    """
    Structured model for extracted document information
    """
    full_name: Optional[str] = Field(None, description="Full name of the individual")
    date_of_birth: Optional[str] = Field(None, description="Date of birth")
    document_type: Optional[str] = Field(None, description="Type of document (ID Card/Birth Certificate)")
    identification_number: Optional[str] = Field(None, description="Unique identification number")
    address: Optional[str] = Field(None, description="Address of the individual")
    additional_details: Optional[Dict[str, str]] = Field(None, description="Any additional extracted information")

class DocumentOCRProcessor:
    """
    Async Document OCR Processor using Langchain and Claude
    """
    def __init__(
        self, 
        model: str = "claude-3-opus-20240229", 
        max_tokens: int = 4096
    ):
        """
        Initialize the OCR processor with Claude model
        
        Args:
            model (str): Claude model to use
            max_tokens (int): Maximum tokens for response
        """
        self.llm = ChatAnthropic(
            model_name=model,
            max_tokens_to_sample=max_tokens,
            anthropic_api_key=settings.anthropic_api_key
        )

    async def process_document(
        self, 
        image_base64: str, 
        document_type: str = "ID Card"
    ) -> DocumentExtractionResult:
        """
        Async method to process a single document image
        
        Args:
            image_base64 (str): Base64 encoded image
            document_type (str): Type of document to process
        
        Returns:
            DocumentExtractionResult: Extracted document information
        """
        prompt = f"""
        You are an expert at extracting information from {document_type} documents.
        Carefully and accurately extract ALL visible text fields. 
        IMPORTANT: 
        - Be precise and structured
        - Extract full name, date of birth, ID number and others
        - If information is partially visible or unclear, mark as None
        - Do NOT hallucinate or make up information
        
        Respond in a clean, structured format focusing on key details.
        """
        
        message_content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            }
        ]
        
        message = HumanMessage(content=message_content)
        
        try:
            response = await asyncio.to_thread(
                self.llm.invoke, 
                [message]
            )
            
            # Basic parsing of response 
            # In production, you might want more robust JSON parsing
            extracted_text = response.content
            
            return DocumentExtractionResult(
                full_name=self._extract_field(extracted_text, "full name"),
                date_of_birth=self._extract_field(extracted_text, "date of birth"),
                document_type=document_type,
                identification_number=self._extract_field(extracted_text, "id number"),
                additional_details={"raw_text": extracted_text}
            )
        
        except Exception as e:
            # Log error in production
            return DocumentExtractionResult(
                additional_details={"error": str(e)}
            )

    def _extract_field(self, text: str, field: str) -> Optional[str]:
        """
        Basic field extraction helper
        
        Args:
            text (str): Full extracted text
            field (str): Field to extract
        
        Returns:
            Optional extracted field value
        """
        # Implement basic extraction logic
        # This is a placeholder and should be enhanced
        return None

class MultiDocumentProcessor:
    """
    Process multiple documents simultaneously
    """
    def __init__(self):
        self.ocr_processor = DocumentOCRProcessor()

    async def process_documents(
        self, 
        images: List[str], 
        document_types: Optional[List[str]] = None
    ) -> List[DocumentExtractionResult]:
        """
        Process multiple documents concurrently
        
        Args:
            images (List[str]): Base64 encoded images
            document_types (Optional[List[str]]): Types of documents
        
        Returns:
            List of extracted document information
        """
        if not document_types:
            document_types = ["ID Card"] * len(images)
        
        tasks = [
            self.ocr_processor.process_document(img, doc_type)
            for img, doc_type in zip(images, document_types)
        ]
        
        return await asyncio.gather(*tasks)

# Utility function for base64 conversion
def encode_image_to_base64(file_path: Union[str, bytes]) -> str:
    """
    Convert image to base64
    
    Args:
        file_path (Union[str, bytes]): Path or bytes of image
    
    Returns:
        Base64 encoded string
    """
    if isinstance(file_path, str):
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    elif isinstance(file_path, bytes):
        return base64.b64encode(file_path).decode('utf-8')
    
    raise ValueError("Invalid image input")