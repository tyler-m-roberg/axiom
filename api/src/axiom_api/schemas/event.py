from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from axiom_api.schemas.common import AuditedMixin


class OnTheFlyFieldSpec(BaseModel):
    """Create an on-the-fly metadata field as part of an event write."""

    key: str
    label: str | None = None
    data_type: str = "string"
    namespace_group_id: str | None = None
    value: Any = None


class EventCreate(BaseModel):
    name: str | None = None
    occurred_at: datetime | None = None
    # { "<field_id>": <value>, ... } for bound fields
    metadata: dict[str, Any] = {}
    on_the_fly: list[OnTheFlyFieldSpec] = []


class EventUpdate(BaseModel):
    name: str | None = None
    occurred_at: datetime | None = None
    metadata: dict[str, Any] | None = None
    on_the_fly: list[OnTheFlyFieldSpec] = []


class EventOut(AuditedMixin):
    test_id: UUID
    name: str | None = None
    occurred_at: datetime | None = None
    metadata: dict[str, Any]
    on_the_fly_field_ids: list[str] = []
