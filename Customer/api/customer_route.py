from fastapi import (
    APIRouter, 
    File, 
    UploadFile, 
    HTTPException, 
    status
)
from typing import List, Optional

from Library.utils import (
    MultiDocumentProcessor, 
    encode_image_to_base64,
    DocumentExtractionResult
)

router = APIRouter(
    prefix="/customer",
    tags=["Customer Document OCR"]
)

@router.post(
    "/extract-documents", 
    response_model=List[DocumentExtractionResult],
    summary="Extract information from ID cards or birth certificates",
    description="Upload 1-2 documents for information extraction"
)
async def extract_document_info(
    documents: List[UploadFile] = File(..., 
        description="1-2 document images to process"),
    document_types: Optional[List[str]] = None
):
    """
    Async endpoint for document information extraction
    
    - Supports 1-2 documents simultaneously
    - Returns structured document information
    - Handles ID cards and birth certificates
    """
    # Validate file inputs
    if len(documents) > 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 2 documents allowed"
        )
    
    # Validate file types
    allowed_types = {'image/jpeg', 'image/png', 'image/gif'}
    for file in documents:
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
    
    # Read file contents
    image_bases = []
    for file in documents:
        content = await file.read()
        image_bases.append(encode_image_to_base64(content))
    
    # Process documents
    processor = MultiDocumentProcessor()
    results = await processor.process_documents(
        images=image_bases, 
        document_types=document_types
    )
    
    return results