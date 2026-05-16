from typing import Any

from keycloak import KeycloakAdmin, KeycloakOpenIDConnection

from axiom_api.config import settings


def _admin() -> KeycloakAdmin:
    conn = KeycloakOpenIDConnection(
        server_url=settings.keycloak_url,
        client_id=settings.keycloak_client_id,
        client_secret_key=settings.keycloak_client_secret,
        realm_name=settings.keycloak_realm,
        user_realm_name=settings.keycloak_realm,
        verify=False,
    )
    return KeycloakAdmin(connection=conn)


def list_groups() -> list[dict[str, Any]]:
    return _admin().get_groups()


def create_group(name: str) -> dict[str, Any]:
    admin = _admin()
    group_id = admin.create_group({"name": name})
    return admin.get_group(group_id)


def update_group(group_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    admin = _admin()
    admin.update_group(group_id=group_id, payload=payload)
    return admin.get_group(group_id)


def delete_group(group_id: str) -> None:
    _admin().delete_group(group_id)


_bff_client_uuid: str | None = None


def _get_bff_client_uuid(admin: KeycloakAdmin) -> str:
    global _bff_client_uuid
    if _bff_client_uuid is None:
        _bff_client_uuid = admin.get_client_id(settings.keycloak_client_id)
    return _bff_client_uuid


def list_roles() -> list[dict[str, Any]]:
    admin = _admin()
    return admin.get_client_roles(client_id=_get_bff_client_uuid(admin))


def create_role(name: str, description: str | None = None) -> dict[str, Any]:
    admin = _admin()
    cid = _get_bff_client_uuid(admin)
    admin.create_client_role(
        client_role_id=cid,
        payload={"name": name, "description": description or ""},
        skip_exists=True,
    )
    return admin.get_client_role(client_id=cid, role_name=name)


def delete_role(name: str) -> None:
    admin = _admin()
    admin.delete_client_role(client_role_id=_get_bff_client_uuid(admin), role_name=name)


def get_group_by_path(path: str) -> dict[str, Any] | None:
    try:
        return _admin().get_group_by_path(path)
    except Exception:
        return None


def list_user_groups(user_id: str) -> list[dict[str, Any]]:
    return _admin().get_user_groups(user_id=user_id)
