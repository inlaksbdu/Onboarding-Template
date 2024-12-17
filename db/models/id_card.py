from datetime import date
import enum
from typing import List, Optional, TYPE_CHECKING
import uuid
from sqlalchemy import String, Date, Float, Enum, ForeignKey, UUID, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .user import User


class DocumentType(str, enum.Enum):
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVER_LICENSE = "driver_license"


class Gender(str, enum.Enum):
    MALE = "M"
    FEMALE = "F"


class IdCardData(Base):
    __tablename__ = "id_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255))
    date_of_birth: Mapped[date] = mapped_column(Date)
    date_of_issue: Mapped[date] = mapped_column(Date)
    date_of_expiry: Mapped[date] = mapped_column(Date)
    document_number: Mapped[str] = mapped_column(String(100), unique=True)
    id_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True
    )
    nationality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType))
    urls: Mapped[List[str]] = mapped_column(JSON, nullable=False)

    street: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100))

    confidence: Mapped[float] = mapped_column(Float)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="documents")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.confidence = self.calculate_confidence()

    @property
    def age(self):
        today = date.today()
        age = (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )
        return age

    def calculate_confidence(self):
        fields = [
            self.full_name,
            self.date_of_birth,
            self.date_of_issue,
            self.date_of_expiry,
            self.document_number,
            self.id_number,
            self.nationality,
            self.gender,
            self.street,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]
        return len([field for field in fields if field is not None]) / len(fields)
