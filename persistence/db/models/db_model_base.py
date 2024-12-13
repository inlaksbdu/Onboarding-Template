from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    declarative_mixin,
)
from sqlalchemy import DateTime, MetaData
from datetime import datetime
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    metadata = MetaData()

    # @declared_attr.directive
    # def __tablename__(cls) -> str:
    #     return cls.__name__.lower() + "s"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.__dict__})>"


@declarative_mixin
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.__dict__})>"



# from datetime import datetime
# from typing import Optional
# from sqlalchemy.orm import declarative_base
# from sqlalchemy import Column, DateTime, String, Integer
# from pydantic import BaseConfig, BaseModel

# Base = declarative_base()

# # class DbBaseModel(BaseModel):
# #     """
# #     Base model which has auditing details
# #     """

# #     created_at: datetime
# #     updated_at: Optional[datetime]

# #     class Config(BaseConfig):
# #         # allow_population_by_field_name = True
# #         populate_by_name = True
# #         arbitrary_types_allowed = True


# class BaseModel(Base):
#     """
#     Base model which has auditing details
#     """

#     __abstract__ = True
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# # BaseModel = declarative_base()
