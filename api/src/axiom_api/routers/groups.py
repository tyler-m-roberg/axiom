from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from axiom_api.deps import AdminDep, CurrentUserDep
from axiom_api.services import keycloak_admin

router = APIRouter()


class GroupCreate(BaseModel):
    name: str


class GroupUpdate(BaseModel):
    name: str | None = None


class RoleCreate(BaseModel):
    name: str
    description: str | None = None


@router.get("/groups")
def list_groups(user: CurrentUserDep) -> list[dict[str, Any]]:
    return keycloak_admin.list_groups()


@router.post("/groups", status_code=201)
def create_group(payload: GroupCreate, _: AdminDep) -> dict[str, Any]:
    try:
        return keycloak_admin.create_group(payload.name)
    except Exception as exc:
        raise HTTPException(400, f"Failed to create group: {exc}") from exc


@router.patch("/groups/{group_id}")
def update_group(group_id: str, payload: GroupUpdate, _: AdminDep) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if payload.name is not None:
        body["name"] = payload.name
    if not body:
        raise HTTPException(400, "Nothing to update")
    return keycloak_admin.update_group(group_id, body)


@router.delete("/groups/{group_id}", status_code=204)
def delete_group(group_id: str, _: AdminDep) -> None:
    keycloak_admin.delete_group(group_id)


@router.get("/roles")
def list_roles(user: CurrentUserDep) -> list[dict[str, Any]]:
    return keycloak_admin.list_roles()


@router.post("/roles", status_code=201)
def create_role(payload: RoleCreate, _: AdminDep) -> dict[str, Any]:
    return keycloak_admin.create_role(payload.name, payload.description)


@router.delete("/roles/{name}", status_code=204)
def delete_role(name: str, _: AdminDep) -> None:
    keycloak_admin.delete_role(name)
