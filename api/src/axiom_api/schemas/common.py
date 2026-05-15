from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AuditedMixin(ORMModel):
    id: UUID
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None
