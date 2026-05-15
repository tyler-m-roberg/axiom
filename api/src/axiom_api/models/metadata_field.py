import enum
import uuid
from typing import Any

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from axiom_api.models.base import Base, TimestampedMixin


class FieldDataType(str, enum.Enum):
    STRING = "string"
    NUMBER = "number"
    BOOL = "bool"
    DATE = "date"
    ENUM = "enum"


class FieldScope(str, enum.Enum):
    TEST = "test"
    EVENT = "event"
    BOTH = "both"


class FieldStatus(str, enum.Enum):
    ESTABLISHED = "established"
    ON_THE_FLY = "on_the_fly"


class BindingRequirement(str, enum.Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"


class BindingApplies(str, enum.Enum):
    TEST = "test"
    EVENT = "event"


class MetadataField(Base, TimestampedMixin):
    __tablename__ = "metadata_fields"
    __table_args__ = (
        UniqueConstraint("namespace_group_id", "key", name="uq_metadata_fields_namespace_key"),
    )

    key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_type: Mapped[FieldDataType] = mapped_column(
        Enum(FieldDataType, name="field_data_type"), nullable=False, default=FieldDataType.STRING
    )
    enum_values: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    scope: Mapped[FieldScope] = mapped_column(
        Enum(FieldScope, name="field_scope"), nullable=False, default=FieldScope.EVENT
    )
    status: Mapped[FieldStatus] = mapped_column(
        Enum(FieldStatus, name="field_status"), nullable=False, default=FieldStatus.ESTABLISHED
    )
    # Null = shared field; non-null = namespaced to that Keycloak group id
    namespace_group_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)


class TestFieldBinding(Base, TimestampedMixin):
    __tablename__ = "test_field_bindings"
    __table_args__ = (
        UniqueConstraint("test_id", "field_id", "applies_to", name="uq_binding_test_field_scope"),
    )

    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("metadata_fields.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requirement: Mapped[BindingRequirement] = mapped_column(
        Enum(BindingRequirement, name="binding_requirement"),
        nullable=False,
        default=BindingRequirement.OPTIONAL,
    )
    applies_to: Mapped[BindingApplies] = mapped_column(
        Enum(BindingApplies, name="binding_applies"),
        nullable=False,
        default=BindingApplies.EVENT,
    )

    test = relationship("Test", back_populates="bindings")
    field = relationship("MetadataField")
