from typing import Any

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from axiom_api.models.base import Base, TimestampedMixin


class Test(Base, TimestampedMixin):
    __tablename__ = "tests"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_values: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )

    events = relationship("Event", back_populates="test", cascade="all, delete-orphan")
    bindings = relationship(
        "TestFieldBinding", back_populates="test", cascade="all, delete-orphan"
    )
    acls = relationship("TestAcl", back_populates="test", cascade="all, delete-orphan")
