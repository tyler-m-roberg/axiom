from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from axiom_api.deps import CurrentUser
from axiom_api.models.audit import AuditAction, AuditLog


def _normalize(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    return value


def diff(before: dict[str, Any] | None, after: dict[str, Any] | None) -> dict[str, Any]:
    before = before or {}
    after = after or {}
    keys = set(before) | set(after)
    out: dict[str, Any] = {}
    for k in keys:
        if before.get(k) != after.get(k):
            out[k] = {"before": before.get(k), "after": after.get(k)}
    return out


def record(
    db: Session,
    *,
    actor: CurrentUser,
    entity_type: str,
    entity_id: str | UUID,
    action: AuditAction,
    test_id: str | UUID | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> AuditLog:
    before_n = _normalize(before)
    after_n = _normalize(after)
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=str(entity_id),
        test_id=UUID(str(test_id)) if test_id is not None and not isinstance(test_id, UUID) else test_id,
        action=action,
        actor_sub=actor.sub,
        actor_username=actor.username,
        before=before_n,
        after=after_n,
        diff=diff(before_n, after_n) if action == AuditAction.UPDATE else None,
        context=_normalize(context) if context else None,
    )
    db.add(entry)
    return entry
