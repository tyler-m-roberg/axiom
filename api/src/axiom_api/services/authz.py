from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from axiom_api.deps import CurrentUser
from axiom_api.models.test_acl import AclPermission, TestAcl


def caller_group_keys(user: CurrentUser) -> set[str]:
    """All keys (group names + group ids) a caller's ACLs/namespaced fields may match against."""
    return {*user.groups, *user.group_ids}


def can_read_test(db: Session, user: CurrentUser, test_id: UUID) -> bool:
    if user.is_admin:
        return True
    keys = caller_group_keys(user)
    if not keys:
        return False
    stmt = select(TestAcl).where(TestAcl.test_id == test_id, TestAcl.group_id.in_(keys))
    return db.execute(stmt).first() is not None


def can_write_test(db: Session, user: CurrentUser, test_id: UUID) -> bool:
    if user.is_admin:
        return True
    keys = caller_group_keys(user)
    if not keys:
        return False
    stmt = select(TestAcl).where(
        TestAcl.test_id == test_id,
        TestAcl.group_id.in_(keys),
        TestAcl.permission.in_([AclPermission.WRITE, AclPermission.ADMIN]),
    )
    return db.execute(stmt).first() is not None


def require_read(db: Session, user: CurrentUser, test_id: UUID) -> None:
    if not can_read_test(db, user, test_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this test")


def require_write(db: Session, user: CurrentUser, test_id: UUID) -> None:
    if not can_write_test(db, user, test_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No write access to this test")


def accessible_test_ids(db: Session, user: CurrentUser) -> list[UUID] | None:
    """Return None to mean 'all' (admins). Otherwise a list of test ids the caller can read."""
    if user.is_admin:
        return None
    keys = caller_group_keys(user)
    if not keys:
        return []
    rows = db.execute(select(TestAcl.test_id).where(TestAcl.group_id.in_(keys))).all()
    return [r[0] for r in rows]
