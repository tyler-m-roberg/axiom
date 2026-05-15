import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from axiom_api.config import settings


@dataclass
class TokenSet:
    access_token: str
    id_token: str | None
    refresh_token: str | None
    expires_in: int
    raw: dict[str, Any]


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def generate_pkce() -> tuple[str, str]:
    verifier = _b64url(secrets.token_bytes(48))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def authorize_url(state: str, code_challenge: str, redirect_uri: str) -> str:
    params = {
        "client_id": settings.keycloak_client_id,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{settings.keycloak_public_realm_url}/protocol/openid-connect/auth?{urlencode(params)}"


async def exchange_code(code: str, code_verifier: str, redirect_uri: str) -> TokenSet:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{settings.keycloak_realm_url}/protocol/openid-connect/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.keycloak_client_id,
                "client_secret": settings.keycloak_client_secret,
                "code_verifier": code_verifier,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return TokenSet(
            access_token=data["access_token"],
            id_token=data.get("id_token"),
            refresh_token=data.get("refresh_token"),
            expires_in=int(data.get("expires_in", 300)),
            raw=data,
        )


async def refresh_token(refresh_token: str) -> TokenSet:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{settings.keycloak_realm_url}/protocol/openid-connect/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.keycloak_client_id,
                "client_secret": settings.keycloak_client_secret,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return TokenSet(
            access_token=data["access_token"],
            id_token=data.get("id_token"),
            refresh_token=data.get("refresh_token"),
            expires_in=int(data.get("expires_in", 300)),
            raw=data,
        )


async def userinfo(access_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{settings.keycloak_realm_url}/protocol/openid-connect/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def end_session(id_token: str | None, post_logout_redirect: str) -> str:
    base = f"{settings.keycloak_public_realm_url}/protocol/openid-connect/logout"
    params: dict[str, str] = {
        "post_logout_redirect_uri": post_logout_redirect,
        "client_id": settings.keycloak_client_id,
    }
    if id_token:
        params["id_token_hint"] = id_token
    return f"{base}?{urlencode(params)}"
