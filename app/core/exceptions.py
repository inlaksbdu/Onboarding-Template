from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class BaseCustomException(HTTPException):
    def init(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().init(status_code=status_code, detail=detail, headers=headers)

class DocumentVerificationError(BaseCustomException):
    def init(self, detail: str):
        super().init(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document verification failed: {detail}"
        )

class FaceVerificationError(BaseCustomException):
    def init(self, detail: str):
        super().init(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Face verification failed: {detail}"
        )

class AMLScreeningError(BaseCustomException):
    def init(self, detail: str):
        super().init(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"AML screening failed: {detail}"
        )