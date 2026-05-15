from typing import Any

from pydantic import BaseModel

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
    metadata: dict[str, Any]


class TestAclCreate(BaseModel):
    group_id: str
    permission: AclPermission = AclPermission.WRITE


class TestAclOut(AuditedMixin):
    test_id: str
    group_id: str
    permission: AclPermission
