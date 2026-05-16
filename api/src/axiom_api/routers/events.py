from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from axiom_api.deps import CurrentUserDep, DbDep
from axiom_api.models.audit import AuditAction
from axiom_api.models.event import Event
from axiom_api.models.test import Test
from axiom_api.schemas.event import EventCreate, EventOut, EventUpdate
from axiom_api.services import audit
from axiom_api.services.authz import require_read, require_write
from axiom_api.services.metadata import (
    filter_event_metadata_for_caller,
    load_fields_by_ids,
    upsert_on_the_fly_fields,
    validate_event_metadata,
)

router = APIRouter()


def _serialize_event(ev: Event, user, db) -> dict:
    fields = load_fields_by_ids(db, [UUID(k) for k in ev.metadata_values.keys() if _is_uuid(k)])
    filtered = filter_event_metadata_for_caller(ev.metadata_values, fields, user)
    return {
        "id": ev.id,
        "test_id": ev.test_id,
        "name": ev.name,
        "occurred_at": ev.occurred_at,
        "metadata": filtered,
        "on_the_fly_field_ids": ev.on_the_fly_field_ids or [],
        "created_at": ev.created_at,
        "created_by": ev.created_by,
        "updated_at": ev.updated_at,
        "updated_by": ev.updated_by,
    }


def _is_uuid(s: str) -> bool:
    try:
        UUID(s)
        return True
    except (ValueError, AttributeError):
        return False


@router.get("/tests/{test_id}/events", response_model=list[EventOut])
def list_events(test_id: UUID, user: CurrentUserDep, db: DbDep) -> list[dict]:
    test = db.get(Test, test_id)
    if not test or test.deleted_at:
        raise HTTPException(404, "Test not found")
    require_read(db, user, test_id)
    rows = list(
        db.execute(
            select(Event)
            .where(Event.test_id == test_id, Event.deleted_at.is_(None))
            .order_by(Event.created_at.asc())
        ).scalars()
    )
    return [_serialize_event(ev, user, db) for ev in rows]


@router.post("/tests/{test_id}/events", response_model=EventOut, status_code=201)
def create_event(
    test_id: UUID, payload: EventCreate, user: CurrentUserDep, db: DbDep
) -> dict:
    test = db.get(Test, test_id)
    if not test or test.deleted_at:
        raise HTTPException(404, "Test not found")
    require_write(db, user, test_id)

    on_the_fly_fields = upsert_on_the_fly_fields(db, user=user, specs=payload.on_the_fly)
    metadata = dict(payload.metadata)
    for spec in payload.on_the_fly:
        if spec.value is None:
            continue
        metadata[str(on_the_fly_fields[spec.key].id)] = spec.value
    validated = validate_event_metadata(db, test_id=test_id, metadata=metadata, user=user)

    ev = Event(
        test_id=test_id,
        name=payload.name,
        occurred_at=payload.occurred_at,
        metadata_values=validated,
        on_the_fly_field_ids=[str(f.id) for f in on_the_fly_fields.values()],
        created_by=user.username,
        updated_by=user.username,
    )
    db.add(ev)
    db.flush()
    audit.record(
        db, actor=user, entity_type="event", entity_id=ev.id, test_id=test_id,
        action=AuditAction.CREATE,
        after={"test_id": str(test_id), "name": ev.name, "metadata": validated},
    )
    db.commit()
    return _serialize_event(ev, user, db)


@router.patch("/events/{event_id}", response_model=EventOut)
def update_event(
    event_id: UUID, payload: EventUpdate, user: CurrentUserDep, db: DbDep
) -> dict:
    ev = db.get(Event, event_id)
    if not ev or ev.deleted_at:
        raise HTTPException(404, "Event not found")
    require_write(db, user, ev.test_id)
    before = {"name": ev.name, "metadata": ev.metadata_values}

    on_the_fly_fields = upsert_on_the_fly_fields(db, user=user, specs=payload.on_the_fly)
    new_otf_ids = list(set(ev.on_the_fly_field_ids or []) | {str(f.id) for f in on_the_fly_fields.values()})

    if payload.metadata is not None:
        merged = dict(payload.metadata)
        for spec in payload.on_the_fly:
            if spec.value is None:
                continue
            merged[str(on_the_fly_fields[spec.key].id)] = spec.value
        # Merge with existing values the caller cannot see (preserve namespaced data)
        from axiom_api.services.metadata import caller_visible_namespace_ids
        visible = caller_visible_namespace_ids(user)
        all_field_ids = [UUID(k) for k in {*ev.metadata_values.keys(), *merged.keys()} if _is_uuid(k)]
        fields_by_id = load_fields_by_ids(db, all_field_ids)
        preserved: dict = {}
        if not user.is_admin:
            for fid, value in ev.metadata_values.items():
                field = fields_by_id.get(str(fid))
                if field and field.namespace_group_id is not None and field.namespace_group_id not in visible:
                    preserved[str(fid)] = value
        validated = validate_event_metadata(db, test_id=ev.test_id, metadata=merged, user=user)
        ev.metadata_values = {**preserved, **validated}

    if payload.name is not None:
        ev.name = payload.name
    if payload.occurred_at is not None:
        ev.occurred_at = payload.occurred_at
    ev.on_the_fly_field_ids = new_otf_ids
    ev.updated_by = user.username

    audit.record(
        db, actor=user, entity_type="event", entity_id=ev.id, test_id=ev.test_id,
        action=AuditAction.UPDATE,
        before=before, after={"name": ev.name, "metadata": ev.metadata_values},
    )
    db.commit()
    return _serialize_event(ev, user, db)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: UUID, user: CurrentUserDep, db: DbDep) -> None:
    ev = db.get(Event, event_id)
    if not ev or ev.deleted_at:
        raise HTTPException(404, "Event not found")
    require_write(db, user, ev.test_id)
    from datetime import datetime, timezone
    ev.deleted_at = datetime.now(tz=timezone.utc)
    ev.updated_by = user.username
    audit.record(
        db, actor=user, entity_type="event", entity_id=ev.id, test_id=ev.test_id,
        action=AuditAction.DELETE, before={"name": ev.name},
    )
    db.commit()
