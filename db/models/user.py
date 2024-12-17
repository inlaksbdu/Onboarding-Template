from typing import TYPE_CHECKING

from datetime import datetime
import enum
import uuid
from sqlalchemy import String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.dialects.postgresql import UUID

from .base import Base

if TYPE_CHECKING:
    from .refresh import RefreshToken
    from .id_card import IdCardData


class UserRole(enum.StrEnum):
    ADMIN = "admin"
    USER = "user"
    BANNED = "banned"


class AccountType(enum.StrEnum):
    INDIVIDUAL = "individual"
    GROUP = "group"
    SME = "sme"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    account_type: Mapped[AccountType] = mapped_column(
        ENUM(AccountType, name="accounttype"), default=AccountType.INDIVIDUAL
    )
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_logged_in: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[UserRole] = mapped_column(
        ENUM(UserRole, name="user_role"), default=UserRole.USER
    )
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    documents: Mapped[list["IdCardData"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    def add_document(self, document: "IdCardData"):
        if self.account_type != AccountType.GROUP and len(self.documents) >= 1:
            raise ValueError("Only group accounts can have multiple ID documents.")
        self.documents.append(document)
