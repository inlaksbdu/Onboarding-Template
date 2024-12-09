from pydantic import BaseModel, EmailStr
from typing import Optional

class CustomerCreateRequest(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None 
    phone: Optional[str] = None
    address: Optional[str] = None