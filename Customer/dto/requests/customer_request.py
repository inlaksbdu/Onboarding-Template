from pydantic import BaseModel, EmailStr
from typing import Optional
import pycountry
from pydantic import EmailStr, constr, Field, field_validator
from typing import Optional, List
from Customer.dto.rwmodel import RWModel
from Customer.dto.validators.validate_password import validate_password
from Customer.dto.validators.validate_phone import validate_phone

from pydantic import BaseModel, EmailStr, Field


class CustomerCreateRequest(BaseModel):
    # Mandatory fields
    first_name: str = Field(description="First name from the document")
    password: str = Field(description="Password of the customer")
    last_name: str = Field(description="Last name from the document")
    date_of_birth: str = Field(
        description="Date of birth in the format shown on document"
    )
    document_type: str = Field(
        description="Type of document (ID Card/Birth Certificate)"
    )
    identification_number: str = Field(
        description="Any ID number or document number shown"
    )
    nationality: Optional[str] = Field(
        default=None, description="Nationality of the individual"
    )
    id_card_issue_date: str = Field(
        description="The date the card or document was issued to the individual"
    )
    id_card_expiry_date: str = Field(
        description="The date the card or document is expected to expire"
    )

    # Optional fields
    email: EmailStr = Field(description="Email address of the individual")
    phone_number: Optional[constr(max_length=15, strip_whitespace=True)] = None
    address: Optional[str] = Field(
        default=None, description="Residential address of the individual"
    )
    where_born: Optional[str] = Field(
        default=None, description="The location where the individual was born"
    )
    father_name: Optional[str] = Field(
        default=None, description="Father's name if shown on document"
    )
    father_occupation: Optional[str] = Field(
        default=None, description="Father's occupation if shown on document"
    )
    mother_name: Optional[str] = Field(
        default=None, description="Mother's name if shown on document"
    )
    mother_occupation: Optional[str] = Field(
        default=None, description="Mother's occupation if shown on document"
    )
    birth_certificate_margin_number: Optional[str] = Field(
        default=None, description="Birth Certificate Margin Number"
    )
    birth_certificate_registration_date: Optional[str] = Field(
        default=None, description="Birth Certificate Registration Date"
    )

    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01",
                "document_type": "ID Card",
                "identification_number": "123456789",
                "nationality": "Ghanaian",
                "id_card_issue_date": "2015-01-01",
                "id_card_expiry_date": "2025-01-01",
                "email": "johndoe@example.com",
                "phone_number": "+233555123456",
                "address": "123 Main Street, Accra",
                "where_born": "Accra",
                "father_name": "Michael Doe",
                "father_occupation": "Engineer",
                "mother_name": "Jane Doe",
                "mother_occupation": "Teacher",
                "birth_certificate_margin_number": "BC12345",
                "birth_certificate_registration_date": "1990-02-01",
            }
        }

    # Validators
    @field_validator("phone_number")
    def check_phone_number(cls, phone_number):
        if phone_number is not None:
            return validate_phone(phone_number)
        return phone_number

    @field_validator("password")
    def validate_password_for_medium_strength(cls, password):
        return validate_password(password)


class CustomerUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
