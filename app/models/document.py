from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base_class import Base

class DocumentType(str, enum.Enum):
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVERS_LICENSE = "drivers_license"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"

class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Document metadata
    document_type = Column(Enum(DocumentType), nullable=False)
    document_number = Column(String(100), nullable=True)
    issuing_country = Column(String(100), nullable=True)
    issue_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # File information
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_type = Column(String(50), nullable=False)  # mime type
    
    # Verification status
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    verification_data = Column(JSON, nullable=True)  # Stores verification service response
    ocr_data = Column(JSON, nullable=True)  # Stores extracted text/data
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    
    # Relationship
    customer = relationship("Customer", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.document_type} - {self.document_number}>"