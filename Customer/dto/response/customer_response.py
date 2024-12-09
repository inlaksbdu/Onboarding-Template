from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class CustomerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str]
    address: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
