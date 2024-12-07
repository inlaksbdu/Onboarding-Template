from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base_class import Base

class VerificationType(str, enum.Enum):
    DOCUMENT = "document"
    FACE = "face"
    LIVENESS = "liveness"
    CREDIT = "credit"
    AML = "aml"
    EMAIL = "email"
    PHONE = "phone"

class VerificationResult(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"

class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Verification details
    verification_type = Column(Enum(VerificationType), nullable=False)
    verification_service = Column(String(100), nullable=False)  # e.g., "jumio", "onfido", "azure"
    result = Column(Enum(VerificationResult), nullable=False)
    
    # Response data
    response_data = Column(JSON, nullable=True)  # Store the full response
    error_message = Column(String(512), nullable=True)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    customer = relationship("Customer", back_populates="verification_logs")

    def __repr__(self):
        return f"<VerificationLog {self.verification_type} - {self.result}>"
