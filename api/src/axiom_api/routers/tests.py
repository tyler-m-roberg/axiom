from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from axiom_api.deps import CurrentUserDep, DbDep
from axiom_api.models.audit import AuditAction
from axiom_api.models.test import Test
from axiom_api.models.test_acl import TestAcl
from axiom_api.schemas.test import (
    TestAclCreate,
    TestAclOut,
    TestCreate,
    TestOut,
    TestUpdate,
)
from axiom_api.services import audit
from axiom_api.services.authz import (
    accessible_test_ids,
    can_read_test,
    require_read,
    require_write,
)

router = APIRouter()


@router.get("", response_model=list[TestOut])
def list_tests(user: CurrentUserDep, db: DbDep) -> list[Test]:
    ids = accessible_test_ids(db, user)
    stmt = select(Test).where(Test.deleted_at.is_(None))
    if ids is not None:
        if not ids:
            return []
        stmt = stmt.where(Test.id.in_(ids))
    return list(db.execute(stmt.order_by(Test.created_at.desc())).scalars())


@router.post("", response_model=TestOut, status_code=status.HTTP_201_CREATED)
def create_test(payload: TestCreate, user: CurrentUserDep, db: DbDep) -> Test:
    obj = Test(
        name=payload.name,
        description=payload.description,
        metadata_values=payload.metadata,
        created_by=user.username,
        updated_by=user.username,
    )
    db.add(obj)
    db.flush()
    audit.record(
        db,
        actor=user,
        entity_type="test",
        entity_id=obj.id,
        test_id=obj.id,
        action=AuditAction.CREATE,
        after={"name": obj.name, "description": obj.description, "metadata": payload.metadata},
    )
    db.commit()
    return obj


@router.get("/{test_id}", response_model=TestOut)
def get_test(test_id: UUID, user: CurrentUserDep, db: DbDep) -> Test:
    obj = db.get(Test, test_id)
    if not obj or obj.deleted_at:
        raise HTTPException(404, "Test not found")
    require_read(db, user, test_id)
    return obj


@router.patch("/{test_id}", response_model=TestOut)
def update_test(test_id: UUID, payload: TestUpdate, user: CurrentUserDep, db: DbDep) -> Test:
    obj = db.get(Test, test_id)
    if not obj or obj.deleted_at:
        raise HTTPException(404, "Test not found")
    require_write(db, user, test_id)
    before = {"name": obj.name, "description": obj.description, "metadata": obj.metadata_values}
    if payload.name is not None:
        obj.name = payload.name
    if payload.description is not None:
        obj.description = payload.description
    if payload.metadata is not None:
        obj.metadata_values = payload.metadata
    obj.updated_by = user.username
    after = {"name": obj.name, "description": obj.description, "metadata": obj.metadata_values}
    audit.record(
        db, actor=user, entity_type="test", entity_id=obj.id, test_id=obj.id,
        action=AuditAction.UPDATE, before=before, after=after,
    )
    db.commit()
    return obj


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test(test_id: UUID, user: CurrentUserDep, db: DbDep) -> None:
    obj = db.get(Test, test_id)
    if not obj or obj.deleted_at:
        raise HTTPException(404, "Test not found")
    require_write(db, user, test_id)
    from datetime import datetime, timezone
    obj.deleted_at = datetime.now(tz=timezone.utc)
    obj.updated_by = user.username
    audit.record(
        db, actor=user, entity_type="test", entity_id=obj.id, test_id=obj.id,
        action=AuditAction.DELETE, before={"name": obj.name},
    )
    db.commit()


# ----- ACLs -----

@router.get("/{test_id}/acls", response_model=list[TestAclOut])
def list_acls(test_id: UUID, user: CurrentUserDep, db: DbDep) -> list[TestAcl]:
    require_read(db, user, test_id)
    return list(db.execute(select(TestAcl).where(TestAcl.test_id == test_id)).scalars())


@router.post("/{test_id}/acls", response_model=TestAclOut, status_code=201)
def add_acl(
    test_id: UUID, payload: TestAclCreate, user: CurrentUserDep, db: DbDep
) -> TestAcl:
    if not user.is_admin:
        # Test-level admins (acls with permission=admin) can also manage ACLs
        require_write(db, user, test_id)
    acl = TestAcl(
        test_id=test_id,
        group_id=payload.group_id,
        permission=payload.permission,
        created_by=user.username,
        updated_by=user.username,
    )
    db.add(acl)
    db.flush()
    audit.record(
        db, actor=user, entity_type="test_acl", entity_id=acl.id, test_id=test_id,
        action=AuditAction.CREATE,
        after={"test_id": str(test_id), "group_id": payload.group_id, "permission": payload.permission.value},
    )
    db.commit()
    return acl


@router.delete("/{test_id}/acls/{acl_id}", status_code=204)
def delete_acl(test_id: UUID, acl_id: UUID, user: CurrentUserDep, db: DbDep) -> None:
    acl = db.get(TestAcl, acl_id)
    if not acl or acl.test_id != test_id:
        raise HTTPException(404, "ACL not found")
    if not user.is_admin:
        require_write(db, user, test_id)
    audit.record(
        db, actor=user, entity_type="test_acl", entity_id=acl.id, test_id=test_id,
        action=AuditAction.DELETE,
        before={"test_id": str(test_id), "group_id": acl.group_id, "permission": acl.permission.value},
    )
    db.delete(acl)
    db.commit()


# ----- Bindings (under /api/tests/{test_id}/bindings) -----

from axiom_api.models.metadata_field import (  # noqa: E402
    BindingRequirement,
    TestFieldBinding,
)
from axiom_api.schemas.metadata_field import (  # noqa: E402
    BindingCreate,
    BindingOut,
    BindingUpdate,
)


@router.get("/{test_id}/bindings", response_model=list[BindingOut])
def list_bindings(test_id: UUID, user: CurrentUserDep, db: DbDep) -> list[TestFieldBinding]:
    require_read(db, user, test_id)
    return list(
        db.execute(select(TestFieldBinding).where(TestFieldBinding.test_id == test_id)).scalars()
    )


@router.post("/{test_id}/bindings", response_model=BindingOut, status_code=201)
def create_binding(
    test_id: UUID, payload: BindingCreate, user: CurrentUserDep, db: DbDep
) -> TestFieldBinding:
    require_write(db, user, test_id)
    binding = TestFieldBinding(
        test_id=test_id,
        field_id=payload.field_id,
        requirement=payload.requirement,
        applies_to=payload.applies_to,
        created_by=user.username,
        updated_by=user.username,
    )
    db.add(binding)
    db.flush()
    audit.record(
        db, actor=user, entity_type="test_field_binding", entity_id=binding.id, test_id=test_id,
        action=AuditAction.CREATE,
        after={
            "test_id": str(test_id),
            "field_id": str(payload.field_id),
            "requirement": payload.requirement.value,
            "applies_to": payload.applies_to.value,
        },
    )
    db.commit()
    return binding


@router.patch("/{test_id}/bindings/{binding_id}", response_model=BindingOut)
def update_binding(
    test_id: UUID,
    binding_id: UUID,
    payload: BindingUpdate,
    user: CurrentUserDep,
    db: DbDep,
) -> TestFieldBinding:
    require_write(db, user, test_id)
    binding = db.get(TestFieldBinding, binding_id)
    if not binding or binding.test_id != test_id:
        raise HTTPException(404, "Binding not found")
    before = {"requirement": binding.requirement.value}
    promoted = binding.requirement != payload.requirement
    binding.requirement = payload.requirement
    binding.updated_by = user.username
    audit.record(
        db, actor=user, entity_type="test_field_binding", entity_id=binding.id, test_id=test_id,
        action=AuditAction.PROMOTE if promoted else AuditAction.UPDATE,
        before=before, after={"requirement": payload.requirement.value},
    )
    db.commit()
    return binding


@router.delete("/{test_id}/bindings/{binding_id}", status_code=204)
def delete_binding(
    test_id: UUID, binding_id: UUID, user: CurrentUserDep, db: DbDep
) -> None:
    require_write(db, user, test_id)
    binding = db.get(TestFieldBinding, binding_id)
    if not binding or binding.test_id != test_id:
        raise HTTPException(404, "Binding not found")
    audit.record(
        db, actor=user, entity_type="test_field_binding", entity_id=binding.id, test_id=test_id,
        action=AuditAction.DELETE,
        before={
            "test_id": str(test_id),
            "field_id": str(binding.field_id),
            "requirement": binding.requirement.value,
        },
    )
    db.delete(binding)
    db.commit()
