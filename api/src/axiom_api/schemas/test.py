from typing import Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field

from axiom_api.models.test_acl import AclPermission
from axiom_api.schemas.common import AuditedMixin


class TestCreate(BaseModel):
    name: str
    description: str | None = None
    metadata: dict[str, Any] = {}


class TestUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None


class TestOut(AuditedMixin):
    name: str
    description: str | None = None
    metadata: dict[str, Any] = Field(
        validation_alias=AliasChoices("metadata_values", "metadata")
    )


class TestAclCreate(BaseModel):
    group_id: str
    permission: AclPermission = AclPermission.WRITE


class TestAclOut(AuditedMixin):
    test_id: UUID
    group_id: str
    permission: AclPermission
