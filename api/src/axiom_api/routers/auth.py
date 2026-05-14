import secrets
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from axiom_api.config import settings
from axiom_api.deps import CurrentUserDep, DbDep
from axiom_api.services import oidc
from axiom_api.services.session_store import (
    create_session,
    delete_session,
    get_session,
    session_id_token,
)

router = APIRouter()

# In-memory store for short-lived OIDC state (state -> (code_verifier, return_to))
# Acceptable for a dev BFF; a multi-instance deployment would move this to Redis or DB.
_oidc_state: dict[str, tuple[str, str]] = {}

REDIRECT_URI = f"{settings.api_public_url}/api/auth/callback"


@router.get("/login")
async def login(return_to: str | None = None) -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    verifier, challenge = oidc.generate_pkce()
    _oidc_state[state] = (verifier, return_to or settings.web_public_url)
    url = oidc.authorize_url(state=state, code_challenge=challenge, redirect_uri=REDIRECT_URI)
    return RedirectResponse(url=url, status_code=302)


@router.get("/callback")
async def callback(
    db: DbDep,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    if error:
        raise HTTPException(status_code=400, detail=f"OIDC error: {error}")
    if not code or not state or state not in _oidc_state:
        raise HTTPException(status_code=400, detail="Invalid OIDC state")
    verifier, return_to = _oidc_state.pop(state)

    tokens = await oidc.exchange_code(code=code, code_verifier=verifier, redirect_uri=REDIRECT_URI)
    user_claims: dict[str, Any] = await oidc.userinfo(tokens.access_token)
    # Merge any access-token-only claims (e.g. realm_access.roles) we want to surface in /me
    # via the raw token: claims are populated server-side; access token never reaches SPA.
    try:
        import base64
        import json

        payload = tokens.access_token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        access_claims = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
        if isinstance(access_claims.get("realm_access"), dict):
            user_claims["realm_access"] = access_claims["realm_access"]
        if isinstance(access_claims.get("groups"), list):
            user_claims["groups"] = access_claims["groups"]
    except Exception:
        pass

    sess = create_session(db, tokens=tokens, claims=user_claims)

    response = RedirectResponse(url=return_to, status_code=302)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=sess.sid,
        max_age=settings.session_lifetime_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    return response


@router.get("/me")
async def me(user: CurrentUserDep) -> dict[str, Any]:
    return {
        "sub": user.sub,
        "username": user.username,
        "email": user.email,
        "groups": user.groups,
        "roles": user.roles,
        "is_admin": user.is_admin,
    }


@router.post("/logout")
async def logout(
    db: DbDep,
    sid: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> JSONResponse:
    id_token: str | None = None
    if sid:
        sess = get_session(db, sid)
        if sess:
            id_token = session_id_token(sess)
            delete_session(db, sid)

    logout_url = await oidc.end_session(
        id_token=id_token, post_logout_redirect=settings.web_public_url
    )
    response = JSONResponse({"logout_url": logout_url})
    response.delete_cookie(settings.session_cookie_name, path="/")
    return response
