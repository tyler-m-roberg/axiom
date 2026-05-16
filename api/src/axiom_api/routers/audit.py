from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import select

from axiom_api.deps import CurrentUserDep, DbDep
from axiom_api.models.audit import AuditLog
from axiom_api.services.authz import accessible_test_ids

router = APIRouter()


@router.get("")
def list_audit(
    user: CurrentUserDep,
    db: DbDep,
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor: str | None = None,
    since: datetime | None = None,
    limit: int = Query(100, le=500),
) -> list[dict[str, Any]]:
    ids = accessible_test_ids(db, user)
    if ids is not None:
        if not ids:
            return []
        stmt = (
            select(AuditLog)
            .where(AuditLog.test_id.in_(ids))
            .order_by(AuditLog.at.desc())
            .limit(limit)
        )
    else:
        stmt = select(AuditLog).order_by(AuditLog.at.desc()).limit(limit)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if actor:
        stmt = stmt.where(AuditLog.actor_username == actor)
    if since:
        stmt = stmt.where(AuditLog.at >= since)
    rows = list(db.execute(stmt).scalars())
    return [
        {
            "id": str(r.id),
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "test_id": str(r.test_id) if r.test_id else None,
            "action": r.action.value,
            "actor_sub": r.actor_sub,
            "actor_username": r.actor_username,
            "at": r.at,
            "before": r.before,
            "after": r.after,
            "diff": r.diff,
            "context": r.context,
        }
        for r in rows
    ]
