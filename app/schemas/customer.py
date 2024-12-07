from pydantic import BaseModel, EmailStr, constr, validator, Field
from datetime import datetime
from typing import Optional, List
from app.models.customer import VerificationStatus

class CustomerBase(BaseModel):
    email: EmailStr
    first_name: constr(min_length=2, max_length=50)
    last_name: constr(min_length=2, max_length=50)
    phone_number: constr(regex=r'^\+?1?\d{9,15}$')
    date_of_birth: datetime
    address: constr(min_length=5, max_length=255)
    city: constr(min_length=2, max_length=100)
    state: constr(min_length=2, max_length=100)
    country: constr(min_length=2, max_length=100)
    postal_code: constr(min_length=2, max_length=20)

    @validator('date_of_birth')
    def validate_birth_date(cls, v):
        if v > datetime.now():
            raise ValueError('Birth date cannot be in the future')
        return v

class CustomerCreate(CustomerBase):
    password: constr(min_length=8, regex=r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$')
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class CustomerUpdate(BaseModel):
    first_name: Optional[constr(min_length=2, max_length=50)] = None
    last_name: Optional[constr(min_length=2, max_length=50)] = None
    phone_number: Optional[constr(regex=r'^\+?1?\d{9,15}$')] = None
    address: Optional[constr(min_length=5, max_length=255)] = None
    city: Optional[constr(min_length=2, max_length=100)] = None
    state: Optional[constr(min_length=2, max_length=100)] = None
    country: Optional[constr(min_length=2, max_length=100)] = None
    postal_code: Optional[constr(min_length=2, max_length=20)] = None

class CustomerInDB(CustomerBase):
    id: int
    is_email_verified: bool
    is_phone_verified: bool
    verification_status: VerificationStatus
    id_document_type: Optional[str]
    id_document_number: Optional[str]
    id_document_expiry: Optional[datetime]
    id_verification_status: VerificationStatus
    face_verification_status: VerificationStatus
    face_verification_score: Optional[int]
    credit_check_status: VerificationStatus
    credit_score: Optional[int]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class CustomerResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    verification_status: VerificationStatus
    created_at: datetime

    class Config:
        from_attributes = True

class CustomerVerificationStatus(BaseModel):
    customer_id: int
    verification_type: str
    status: VerificationStatus
    message: Optional[str] = None

class CustomerSearch(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    document_number: Optional[str] = None
    verification_status: Optional[VerificationStatus] = None

class ChangePassword(BaseModel):
    current_password: str
    new_password: constr(min_length=8, regex=r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$')
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v