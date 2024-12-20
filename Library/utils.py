import base64
import asyncio
from typing import List, Optional, Dict, Union
from pydantic import BaseModel, Field, ConfigDict
from Library.config import settings
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
import os

class DocumentInfo(BaseModel):
    """
    Structured model for document information extraction
    """
    model_config = ConfigDict(extra='forbid')
    
    full_name: str = Field(description="Full name from the document (combine surname and firstname if separate)")
    date_of_birth: str = Field(description="Date of birth in the format shown on document")
    document_type: str = Field(description="Type of document (ID Card/Birth Certificate)")
    identification_number: str = Field(description="Any ID number or document number shown")
    nationality: Optional[str] = Field(default=None, description="Nationality of the individual")
    gender: Optional[str] = Field(default=None, description="Gender/Sex of the individual")
    address: Optional[str] = Field(default=None, description="Address if shown on document")
    raw_text: str = Field(description="The complete raw text extracted from the document")

    id_card_issue_date: str= Field(description="the Date the card or document was issued to the individual")
    id_card_expiry_date: str= Field(description="the Date the card or document is expected to expire")
    where_born: str = Field(description="the Location where the individual was born")
    father_name: Optional[str] = Field(default=None, description="Father's name if shown on document")
    father_occupation: Optional[str] = Field(default=None, description="Father's occupation if shown on document")
    mother_name: Optional[str] = Field(default=None, description="Mother's name if shown on document")
    mother_occupation: Optional[str] = Field(default=None, description="Mother's occupation if shown on document")
    # Birth Certificate Information
    birth_certificate_margin_number: Optional[str] = Field(default=None, description="Birth Certificate Margin Number")

    birth_certificate_registration_date: Optional[str] = Field(default=None, description="Birth Certificate Registration Date")

class DocumentExtractionResult(BaseModel):
    """
    Final result model that includes both extracted info and any additional details
    """
    model_config = ConfigDict(extra='forbid')
    
    document_info: Optional[DocumentInfo] = Field(default=None, description="Structured document information")
    additional_details: Optional[Dict[str, str]] = Field(default=None, description="Any additional details or error information")

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
        base_model = ChatAnthropic(
            model_name=model,
            max_tokens_to_sample=max_tokens,
            anthropic_api_key=settings.anthropic_api_key
        )
        self.llm = base_model.with_structured_output(DocumentInfo, name="extract_document_info")

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
        Analyze this {document_type} image and extract the required information and return the answer in the language of the document .
        Make sure to extract all visible text fields accurately.
        
        IMPORTANT: 
        - Be precise and structured
        - If information is partially visible or unclear, mark as None
        - Do NOT hallucinate or make up information
        - Preserve the exact format of dates and numbers
        - For names, combine surname and firstname if they are separate
        - Extract any ID numbers or document numbers shown
        
        Call the extract_document_info function with the extracted information.
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
            doc_info = await asyncio.to_thread(
                self.llm.invoke,
                [message]
            )
            
            return DocumentExtractionResult(
                document_info=doc_info,
                additional_details={"status": "success"}
            )
            
        except Exception as e:
            return DocumentExtractionResult(
                additional_details={"error": str(e)}
            )

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