import uuid
from datetime import date
from sqlalchemy import Column, String, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from db.models.db_model_base import Base, TimestampMixin


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    # UUID Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Personal Information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    password = Column(String(50), nullable=False)
    gender = Column(String(6), nullable=False)
    date_of_birth = Column(Date, nullable=False)

    # Contact Information
    email = Column(String(100), unique=True, nullable=False)
    phone_number = Column(String(20), nullable=True)

    # Address
    address_line1 = Column(String(200), nullable=False)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    nationality = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)

    # ID Card Information
    id_card_number = Column(String(50), unique=True, nullable=False)
    document_number = Column(String(50), unique=True, nullable=False)
    id_card_type = Column(
        String(50), nullable=False
    )  # e.g., Passport, Driver's License
    id_card_issue_date = Column(Date, nullable=False)
    id_card_expiry_date = Column(Date, nullable=False)
    where_born = Column(String(100), nullable=True)

    # Birth Certificate Information
    birth_certificate_margin = Column(String(50), unique=True, nullable=False)
    father_name = Column(String(50), nullable=True)
    father_occupation = Column(String(50), nullable=True)
    mother_name = Column(String(50), nullable=True)
    mother_occupation = Column(String(50), nullable=True)
    birth_certificate_issue_date = Column(Date, nullable=False)

    def __repr__(self):
        return f"<Customer {self.first_name} {self.last_name} (ID: {self.id})>"
