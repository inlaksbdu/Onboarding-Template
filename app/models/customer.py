from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from typing import Optional

from app.db.base_class import Base
from app.core.security import get_password_hash

class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    REJECTED = "rejected"

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    
    # Verification fields
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    kyc_data = Column(JSON, nullable=True)  # Stores KYC verification results
    
    # Document verification
    id_document_type = Column(String(50), nullable=True)  # passport, national_id, etc.
    id_document_number = Column(String(50), nullable=True)
    id_document_expiry = Column(DateTime, nullable=True)
    id_verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    
    # Face verification
    face_verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    face_verification_score = Column(Integer, nullable=True)
    
    # Credit check
    credit_check_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    credit_score = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="customer")
    verification_logs = relationship("VerificationLog", back_populates="customer")

    def __init__(self, **kwargs):
        if 'password' in kwargs:
            kwargs['hashed_password'] = get_password_hash(kwargs.pop('password'))
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Customer {self.email}>"
