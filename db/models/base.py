from datetime import UTC, datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import MetaData, DateTime


def curr_timestamp() -> datetime:
    return datetime.now(UTC)


naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=curr_timestamp, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=curr_timestamp,
        onupdate=curr_timestamp,
        nullable=False,
    )

    def to_dict(
        self, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None
    ) -> Dict:
        if include is not None and exclude is not None:
            raise ValueError("Cannot specify both include and exclude")

        result = {}

        for column in self.__table__.columns:
            if exclude and column.name in exclude:
                continue

            if include and column.name not in include:
                continue

            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value

        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "Base":
        return cls(**data)

    @classmethod
    def from_list(cls, data: List[Dict]) -> List["Base"]:
        return [cls.from_dict(item) for item in data]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_dict()})"

    def __str__(self) -> str:
        return self.__repr__()
