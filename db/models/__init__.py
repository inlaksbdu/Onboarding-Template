import uuid
from datetime import date
from sqlalchemy import Column, String, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum as PyEnum


class Customer:
    __tablename__ = "customers"

    # UUID Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Personal Information
    first_name: str = Column(String(50), nullable=False)
    last_name: str = Column(String(50), nullable=False)
    middle_name: str = Column(String(50), nullable=True)
    gender: str = Column(String(50), nullable=True)
    date_of_birth = Column(Date, nullable=True)

    # Contact Information
    email: str = Column(String(100), unique=True, nullable=False)
    phone_number: str = Column(String(20), nullable=True)

    # Address
    address_line1: str = Column(String(200), nullable=False)
    address_line2: str = Column(String(200), nullable=True)
    city: str = Column(String(100), nullable=False)
    state: str = Column(String(100), nullable=False)
    nationality: str = Column(String(100), nullable=False)
    postal_code: str = Column(String(20), nullable=False)

    # ID Card Information
    id_card_number: str = Column(String(50), unique=True, nullable=False)
    document_number: str = Column(String(50), unique=True, nullable=False)
    height: str = Column(String(50), nullable=False)
    id_card_type: str = Column(
        String(50), nullable=False
    )  # e.g., Passport, Driver's License
    id_card_issue_date = Column(Date, nullable=False)
    id_card_expiry_date = Column(Date, nullable=False)

    # Birth Certificate Information
    birth_certificate_margin: str = Column(String(50), unique=True, nullable=True)
    father_name: str = Column(String(50), nullable=True)
    father_nationality: str = Column(String(50), nullable=True)
    mother_name: str = Column(String(50), nullable=True)
    mother_nationality: str = Column(String(50), nullable=True)
    birth_certificate_issue_date = Column(Date, nullable=False)
    birth_certificate_issuing_Registrar: str = Column(String(200), nullable=True)

    def __repr__(self):
        return f"<Customer {self.first_name} {self.last_name} (ID: {self.id})>"
