from typing import Literal, Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


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
    full_name: str = Field(description="Full name as shown on document")
    date_of_birth: date = Field(description="Date of birth in YYYY-MM-DD format")
    date_of_issue: date = Field(description="Document issue date in YYYY-MM-DD format")
    date_of_expiry: date = Field(
        description="Document expiry date in YYYY-MM-DD format"
    )
    document_number: str = Field(description="Unique identifier number of the document")
    id_number: Optional[str] = Field(description="ID number if present on document")
    nationality: Optional[str] = Field(description="Nationality as shown on document")
    gender: Literal["M", "F"] = Field(description="Gender as shown on document")
    address: Optional[Address] = Field(description="Address information if present")
    confidence: float = Field(description="Confidence level of extraction", ge=0, le=1)
