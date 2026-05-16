from dataclasses import dataclass
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from axiom_api.config import settings
from axiom_api.db import get_db
from axiom_api.models.session import OidcSession
from axiom_api.services.session_store import get_session


@dataclass
class CurrentUser:
    sub: str
    username: str
    email: str | None
    groups: list[str]  # Keycloak group names (e.g. "team-a")
    group_ids: list[str]  # Group UUIDs (populated lazily via /me)
    roles: list[str]
    session: OidcSession

    @property
    def is_admin(self) -> bool:
        return "axiom-admin" in self.roles


async def current_user(
    db: Annotated[Session, Depends(get_db)],
    sid: Annotated[str | None, Cookie(alias=settings.session_cookie_name)] = None,
) -> CurrentUser:
    sess = get_session(db, sid)
    if not sess:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    claims = sess.claims or {}
    roles: list[str] = []
    resource_access = claims.get("resource_access")
    if isinstance(resource_access, dict):
        bff_access = resource_access.get(settings.keycloak_client_id)
        if isinstance(bff_access, dict):
            roles = list(bff_access.get("roles", []))
    groups_raw = claims.get("groups", [])
    groups: list[str] = []
    if isinstance(groups_raw, list):
        for g in groups_raw:
            if isinstance(g, str):
                groups.append(g.lstrip("/"))
    return CurrentUser(
        sub=sess.user_sub,
        username=sess.username or "",
        email=sess.email,
        groups=groups,
        group_ids=claims.get("group_ids", []) if isinstance(claims.get("group_ids"), list) else [],
        roles=roles,
        session=sess,
    )


CurrentUserDep = Annotated[CurrentUser, Depends(current_user)]
DbDep = Annotated[Session, Depends(get_db)]


def require_admin(user: CurrentUserDep) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


AdminDep = Annotated[CurrentUser, Depends(require_admin)]
