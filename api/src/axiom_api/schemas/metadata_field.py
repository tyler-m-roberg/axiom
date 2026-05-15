from uuid import UUID

from pydantic import BaseModel, Field

from axiom_api.models.metadata_field import (
    BindingApplies,
    BindingRequirement,
    FieldDataType,
    FieldScope,
    FieldStatus,
)
from axiom_api.schemas.common import AuditedMixin


class MetadataFieldCreate(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    label: str
    description: str | None = None
    data_type: FieldDataType = FieldDataType.STRING
    enum_values: list[str] | None = None
    scope: FieldScope = FieldScope.EVENT
    namespace_group_id: str | None = None
    status: FieldStatus = FieldStatus.ESTABLISHED


class MetadataFieldUpdate(BaseModel):
    label: str | None = None
    description: str | None = None
    enum_values: list[str] | None = None
    scope: FieldScope | None = None
    namespace_group_id: str | None = None
    status: FieldStatus | None = None


class MetadataFieldOut(AuditedMixin):
    key: str
    label: str
    description: str | None = None
    data_type: FieldDataType
    enum_values: list[str] | None = None
    scope: FieldScope
    status: FieldStatus
    namespace_group_id: str | None = None


class BindingCreate(BaseModel):
    field_id: UUID
    requirement: BindingRequirement = BindingRequirement.OPTIONAL
    applies_to: BindingApplies = BindingApplies.EVENT


class BindingUpdate(BaseModel):
    requirement: BindingRequirement


class BindingOut(AuditedMixin):
    test_id: UUID
    field_id: UUID
    requirement: BindingRequirement
    applies_to: BindingApplies
