"""Unit-level tests for audit permission scoping.

The repo doesn't yet have a Postgres-backed test fixture (the only existing tests
in test_smoke.py operate without a DB). End-to-end behavior for the audit
endpoint is documented in the plan's manual verification step. These tests cover
the in-process pieces: the new column, the `record()` signature, and that the
router builds its query with `accessible_test_ids`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

from axiom_api.deps import CurrentUser
from axiom_api.models.audit import AuditAction, AuditLog
from axiom_api.services import audit as audit_service


@dataclass
class _StubSession:
    added: list[Any]

    def add(self, obj: Any) -> None:
        self.added.append(obj)


def _user(*, admin: bool = False, groups: list[str] | None = None) -> CurrentUser:
    return CurrentUser(
        sub="user-sub",
        username="alice",
        email=None,
        groups=groups or [],
        group_ids=[],
        roles=["axiom-admin"] if admin else ["axiom-user"],
        session=MagicMock(),
    )


def test_audit_log_has_test_id_column() -> None:
    assert "test_id" in AuditLog.__table__.columns
    col = AuditLog.__table__.columns["test_id"]
    assert col.nullable is True
    assert col.index is True


def test_record_persists_test_id_uuid() -> None:
    db = _StubSession(added=[])
    tid = uuid.uuid4()
    eid = uuid.uuid4()
    audit_service.record(
        db,  # type: ignore[arg-type]
        actor=_user(),
        entity_type="event",
        entity_id=eid,
        test_id=tid,
        action=AuditAction.CREATE,
        after={"name": "x"},
    )
    [entry] = db.added
    assert isinstance(entry, AuditLog)
    assert entry.test_id == tid
    assert entry.entity_id == str(eid)


def test_record_accepts_string_test_id() -> None:
    db = _StubSession(added=[])
    tid = uuid.uuid4()
    audit_service.record(
        db,  # type: ignore[arg-type]
        actor=_user(),
        entity_type="test_acl",
        entity_id=uuid.uuid4(),
        test_id=str(tid),
        action=AuditAction.CREATE,
    )
    [entry] = db.added
    assert entry.test_id == tid


def test_record_defaults_test_id_to_none_for_global_entities() -> None:
    db = _StubSession(added=[])
    audit_service.record(
        db,  # type: ignore[arg-type]
        actor=_user(admin=True),
        entity_type="metadata_field",
        entity_id=uuid.uuid4(),
        action=AuditAction.CREATE,
    )
    [entry] = db.added
    assert entry.test_id is None


def test_audit_endpoint_uses_accessible_test_ids() -> None:
    """The audit router must scope via accessible_test_ids — not return everything."""
    import inspect

    from axiom_api.routers import audit as audit_router

    source = inspect.getsource(audit_router.list_audit)
    assert "accessible_test_ids" in source, (
        "list_audit must filter by accessible_test_ids() to scope non-admin results"
    )
    assert "AuditLog.test_id" in source, (
        "list_audit must filter on AuditLog.test_id for non-admin callers"
    )
