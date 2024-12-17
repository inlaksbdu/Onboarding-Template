from pydantic import BaseModel, EmailStr
from typing import Optional
from pydantic import EmailStr, Field
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CustomerCreateRequest(BaseModel):
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
    issue_date: str = Field(
        description="The date the card or document was issued to the individual"
    )
    expiry_date: str = Field(
        description="The date the card or document is expected to expire"
    )

    # Validators
    # @field_validator("phone_number")
    # def check_phone_number(cls, phone_number):
    #     if phone_number is not None:
    #         return validate_phone(phone_number)
    #     return phone_number

    # @field_validator("password")
    # def validate_password_for_medium_strength(cls, password):
    #     return validate_password(password)


class CustomerUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
