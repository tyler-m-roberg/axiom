import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from axiom_api.config import settings
from axiom_api.models.session import OidcSession
from axiom_api.services.crypto import decrypt, encrypt
from axiom_api.services.oidc import TokenSet


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_session(
    db: Session,
    *,
    tokens: TokenSet,
    claims: dict[str, Any],
) -> OidcSession:
    sid = secrets.token_urlsafe(32)
    sess = OidcSession(
        sid=sid,
        user_sub=claims.get("sub", ""),
        username=claims.get("preferred_username"),
        email=claims.get("email"),
        claims=claims,
        id_token_enc=encrypt(tokens.id_token),
        access_token_enc=encrypt(tokens.access_token),
        refresh_token_enc=encrypt(tokens.refresh_token),
        expires_at=_now() + timedelta(seconds=settings.session_lifetime_seconds),
    )
    db.add(sess)
    db.commit()
    return sess


def get_session(db: Session, sid: str | None) -> OidcSession | None:
    if not sid:
        return None
    sess = db.get(OidcSession, sid)
    if not sess:
        return None
    if sess.expires_at < _now():
        db.delete(sess)
        db.commit()
        return None
    sess.last_seen_at = _now()
    db.commit()
    return sess


def delete_session(db: Session, sid: str) -> None:
    sess = db.get(OidcSession, sid)
    if sess:
        db.delete(sess)
        db.commit()


def session_access_token(sess: OidcSession) -> str | None:
    return decrypt(sess.access_token_enc)


def session_id_token(sess: OidcSession) -> str | None:
    return decrypt(sess.id_token_enc)
