from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from axiom_api.deps import CurrentUser
from axiom_api.models.metadata_field import (
    BindingApplies,
    BindingRequirement,
    FieldDataType,
    FieldStatus,
    MetadataField,
    TestFieldBinding,
)


def _coerce(value: Any, dtype: FieldDataType) -> Any:
    if value is None:
        return None
    if dtype == FieldDataType.STRING:
        return str(value)
    if dtype == FieldDataType.NUMBER:
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"Expected number, got {value!r}") from exc
    if dtype == FieldDataType.BOOL:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)
    if dtype == FieldDataType.DATE:
        return str(value)
    if dtype == FieldDataType.ENUM:
        return str(value)
    return value


def caller_visible_namespace_ids(user: CurrentUser) -> set[str]:
    """Group ids/names this caller is a member of; used to filter namespaced fields."""
    return {*user.groups, *user.group_ids}


def filter_event_metadata_for_caller(
    event_metadata: dict[str, Any],
    fields_by_id: dict[str, MetadataField],
    user: CurrentUser,
) -> dict[str, Any]:
    if user.is_admin:
        return event_metadata
    visible = caller_visible_namespace_ids(user)
    out: dict[str, Any] = {}
    for field_id, value in event_metadata.items():
        field = fields_by_id.get(str(field_id))
        if field is None:
            # Unknown id — preserve so admins/UI can clean up
            out[field_id] = value
            continue
        if field.namespace_group_id is None or field.namespace_group_id in visible:
            out[field_id] = value
    return out


def load_bindings_for_test(
    db: Session, test_id: UUID, applies_to: BindingApplies | None = None
) -> list[TestFieldBinding]:
    stmt = select(TestFieldBinding).where(TestFieldBinding.test_id == test_id)
    if applies_to is not None:
        stmt = stmt.where(TestFieldBinding.applies_to == applies_to)
    return list(db.execute(stmt).scalars())


def load_fields_by_ids(db: Session, field_ids: list[UUID]) -> dict[str, MetadataField]:
    if not field_ids:
        return {}
    rows = db.execute(select(MetadataField).where(MetadataField.id.in_(field_ids))).scalars()
    return {str(f.id): f for f in rows}


def validate_event_metadata(
    db: Session,
    *,
    test_id: UUID,
    metadata: dict[str, Any],
    user: CurrentUser,
) -> dict[str, Any]:
    """
    Validate per-event metadata against bindings + field types.

    - Requires required-fields that are bound for namespaces the caller belongs to (or shared).
    - Strips writes to namespaced fields the caller is not a member of.
    - Coerces values to field data types.
    """
    bindings = load_bindings_for_test(db, test_id, BindingApplies.EVENT)
    field_ids = [b.field_id for b in bindings]
    field_ids += [UUID(fid) for fid in metadata.keys() if _is_uuid(fid)]
    fields_by_id = load_fields_by_ids(db, field_ids)

    visible = caller_visible_namespace_ids(user)
    out: dict[str, Any] = {}
    # Coerce and namespace-filter caller-supplied values
    for fid, value in metadata.items():
        field = fields_by_id.get(str(fid))
        if field is None:
            raise HTTPException(status_code=422, detail=f"Unknown field id: {fid}")
        if field.namespace_group_id is not None and not user.is_admin and field.namespace_group_id not in visible:
            # Caller can't write into a namespace they don't belong to
            continue
        out[str(fid)] = _coerce(value, field.data_type)

    # Enforce required bindings that apply to this caller
    for b in bindings:
        if b.requirement != BindingRequirement.REQUIRED:
            continue
        field = fields_by_id.get(str(b.field_id))
        if field is None:
            continue
        if field.namespace_group_id is not None and not user.is_admin and field.namespace_group_id not in visible:
            continue
        if str(b.field_id) not in out or out[str(b.field_id)] in (None, ""):
            raise HTTPException(
                status_code=422,
                detail=f"Required field '{field.key}' is missing",
            )

    return out


def _is_uuid(s: str) -> bool:
    try:
        UUID(s)
        return True
    except (ValueError, AttributeError):
        return False


def upsert_on_the_fly_fields(
    db: Session,
    *,
    user: CurrentUser,
    specs: list[Any],  # list[OnTheFlyFieldSpec]
) -> dict[str, MetadataField]:
    """Create on-the-fly metadata fields. Returns {key_in_spec: MetadataField}."""
    visible = caller_visible_namespace_ids(user)
    created: dict[str, MetadataField] = {}
    for spec in specs:
        ns = spec.namespace_group_id
        if ns is not None and not user.is_admin and ns not in visible:
            raise HTTPException(
                status_code=403,
                detail=f"Cannot create on-the-fly field in namespace '{ns}'",
            )
        # Reuse existing if (namespace, key) already exists
        existing = db.execute(
            select(MetadataField).where(
                MetadataField.namespace_group_id == ns, MetadataField.key == spec.key
            )
        ).scalar_one_or_none()
        if existing:
            created[spec.key] = existing
            continue
        try:
            dtype = FieldDataType(spec.data_type)
        except ValueError:
            dtype = FieldDataType.STRING
        field = MetadataField(
            key=spec.key,
            label=spec.label or spec.key,
            data_type=dtype,
            namespace_group_id=ns,
            status=FieldStatus.ON_THE_FLY,
            created_by=user.username,
            updated_by=user.username,
        )
        db.add(field)
        db.flush()
        created[spec.key] = field
    return created
