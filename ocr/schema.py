from typing import Literal, Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


class DocumentInfo(BaseModel):
    """
    Structured model for document information extraction
    """

    first_name: str = Field(description="First name from the document")
    last_name: str = Field(description="Last name from the document")
    date_of_birth: str = Field(
        description="Date of birth in the format shown on document"
    )
    document_type: str = Field(
        description="Type of document (ID Card/Birth Certificate)"
    )
    identification_number: str = Field(description="ID number or document number")
    nationality: Optional[str] = Field(
        default=None, description="Nationality of the individual"
    )
    gender: Optional[str] = Field(
        default=None, description="Gender/Sex of the individual"
    )
    address: Optional[str] = Field(
        default=None, description="Address if shown on document"
    )

    id_card_issue_date: str = Field(
        description="the Date the card or document was issued to the individual"
    )
    id_card_expiry_date: str = Field(
        description="the Date the card or document is expected to expire"
    )
    where_born: str = Field(description="the Location where the individual was born")
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

    model_config = ConfigDict(extra="ignore")


class Address(BaseModel):
    street: str | None = Field(
        None, description="Street address including house/building number"
    )
    city: str = Field(description="City name")
    state: Optional[str] = Field(description="State or province")
    postal_code: Optional[str] = Field(description="Postal or ZIP code")
    country: str = Field(description="Country name")


class IDDocument(BaseModel):
    """
    Structured schema for ID document information extraction
    """

    document_type: Literal["passport", "national_id", "driver_license"] = Field(
        description="Type of ID (passport, national ID, driver's license)"
    )
    document_number: str = Field(description="Unique identifier number of the document")
    full_name: str = Field(description="Full name as shown on document")
    date_of_birth: date = Field(description="Date of birth in YYYY-MM-DD format")
    date_of_issue: date = Field(description="Document issue date in YYYY-MM-DD format")
    date_of_expiry: date = Field(
        description="Document expiry date in YYYY-MM-DD format"
    )
    nationality: Optional[str] = Field(description="Nationality as shown on document")
    gender: Literal["M", "F"] = Field(description="Gender as shown on document")
    address: Optional[Address] = Field(description="Address information if present")
    confidence: float = Field(description="Confidence level of extraction", ge=0, le=1)
