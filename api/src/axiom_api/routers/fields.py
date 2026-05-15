from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from axiom_api.deps import CurrentUserDep, DbDep
from axiom_api.models.audit import AuditAction
from axiom_api.models.metadata_field import FieldStatus, MetadataField
from axiom_api.schemas.metadata_field import (
    MetadataFieldCreate,
    MetadataFieldOut,
    MetadataFieldUpdate,
)
from axiom_api.services import audit
from axiom_api.services.metadata import caller_visible_namespace_ids

router = APIRouter()


def _visible_to_caller(field: MetadataField, user) -> bool:
    if user.is_admin or field.namespace_group_id is None:
        return True
    return field.namespace_group_id in caller_visible_namespace_ids(user)


@router.get("", response_model=list[MetadataFieldOut])
def list_fields(
    user: CurrentUserDep,
    db: DbDep,
    status_filter: FieldStatus | None = Query(None, alias="status"),
    namespace_group_id: str | None = None,
    include_namespaced: bool = True,
) -> list[MetadataField]:
    stmt = select(MetadataField).where(MetadataField.deleted_at.is_(None))
    if status_filter is not None:
        stmt = stmt.where(MetadataField.status == status_filter)
    if namespace_group_id is not None:
        stmt = stmt.where(MetadataField.namespace_group_id == namespace_group_id)
    rows = list(db.execute(stmt.order_by(MetadataField.key.asc())).scalars())
    if not include_namespaced:
        rows = [f for f in rows if f.namespace_group_id is None]
    return [f for f in rows if _visible_to_caller(f, user)]


@router.post("", response_model=MetadataFieldOut, status_code=status.HTTP_201_CREATED)
def create_field(payload: MetadataFieldCreate, user: CurrentUserDep, db: DbDep) -> MetadataField:
    if payload.namespace_group_id is not None and not user.is_admin:
        if payload.namespace_group_id not in caller_visible_namespace_ids(user):
            raise HTTPException(403, "Cannot create field in a namespace you don't belong to")
    field = MetadataField(
        key=payload.key,
        label=payload.label,
        description=payload.description,
        data_type=payload.data_type,
        enum_values=payload.enum_values,
        scope=payload.scope,
        status=payload.status,
        namespace_group_id=payload.namespace_group_id,
        created_by=user.username,
        updated_by=user.username,
    )
    db.add(field)
    db.flush()
    audit.record(
        db, actor=user, entity_type="metadata_field", entity_id=field.id,
        action=AuditAction.CREATE,
        after={
            "key": field.key, "label": field.label, "data_type": field.data_type.value,
            "scope": field.scope.value, "status": field.status.value,
            "namespace_group_id": field.namespace_group_id,
        },
    )
    db.commit()
    return field


@router.patch("/{field_id}", response_model=MetadataFieldOut)
def update_field(
    field_id: UUID, payload: MetadataFieldUpdate, user: CurrentUserDep, db: DbDep
) -> MetadataField:
    field = db.get(MetadataField, field_id)
    if not field or field.deleted_at:
        raise HTTPException(404, "Field not found")
    if not _visible_to_caller(field, user):
        raise HTTPException(403, "Cannot modify a field outside your namespace")

    before = {
        "label": field.label, "description": field.description,
        "scope": field.scope.value, "status": field.status.value,
        "namespace_group_id": field.namespace_group_id,
    }
    promoted = False
    if payload.label is not None:
        field.label = payload.label
    if payload.description is not None:
        field.description = payload.description
    if payload.enum_values is not None:
        field.enum_values = payload.enum_values
    if payload.scope is not None:
        field.scope = payload.scope
    if payload.status is not None:
        if field.status != payload.status and payload.status == FieldStatus.ESTABLISHED:
            promoted = True
        field.status = payload.status
    if payload.namespace_group_id is not None:
        if not user.is_admin:
            raise HTTPException(403, "Only admins can change a field's namespace")
        field.namespace_group_id = payload.namespace_group_id or None
    field.updated_by = user.username

    audit.record(
        db, actor=user, entity_type="metadata_field", entity_id=field.id,
        action=AuditAction.PROMOTE if promoted else AuditAction.UPDATE,
        before=before,
        after={
            "label": field.label, "description": field.description,
            "scope": field.scope.value, "status": field.status.value,
            "namespace_group_id": field.namespace_group_id,
        },
    )
    db.commit()
    return field


@router.delete("/{field_id}", status_code=204)
def delete_field(field_id: UUID, user: CurrentUserDep, db: DbDep) -> None:
    field = db.get(MetadataField, field_id)
    if not field or field.deleted_at:
        raise HTTPException(404, "Field not found")
    if not user.is_admin and not _visible_to_caller(field, user):
        raise HTTPException(403, "Cannot delete a field outside your namespace")
    from datetime import datetime, timezone
    field.deleted_at = datetime.now(tz=timezone.utc)
    field.updated_by = user.username
    audit.record(
        db, actor=user, entity_type="metadata_field", entity_id=field.id,
        action=AuditAction.DELETE, before={"key": field.key},
    )
    db.commit()
