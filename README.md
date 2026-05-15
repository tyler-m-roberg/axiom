# Axiom

A web application for enriching tests/projects and the events that fall under them with structured metadata.

- **Tests** (top-level) contain **events**.
- **Metadata fields** live in a global data dictionary; bindings declare which fields are `required` or `optional` for a given test (at the test or event level).
- Fields can be **shared** or **namespaced to a group** so multiple groups can collaborate on the same event without leaking values across teams.
- Events accept **on-the-fly** fields that can later be promoted into the dictionary; optional bindings can be promoted to required.
- A full audit trail tracks every create/update/delete.
- Authentication uses **Keycloak (OIDC)** via a strict **Backend-for-Frontend** pattern with a confidential client. The SPA never sees OIDC tokens.
- A management UI exposes Keycloak groups and roles and binds groups to per-test ACLs.

## Stack

| Layer | Choice |
| --- | --- |
| Frontend | Vite + React 18 + TypeScript + MUI v6 (dark mode default + toggle) + MUI X DataGrid |
| API / BFF | Python 3.12 + FastAPI + SQLAlchemy 2.x + Alembic + Pydantic v2 |
| DB | PostgreSQL 16 (JSONB metadata) |
| Auth | Keycloak 24, OIDC Authorization Code + PKCE, confidential client |
| Dev infra | Docker Compose |

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Then open:

- Web app: http://localhost:5173
- API: http://localhost:8000 (docs at `/docs`)
- Keycloak admin: http://localhost:8080 (admin / admin)

The Keycloak `axiom` realm is auto-imported with:

- Confidential client `axiom-bff` (secret in `.env.example` — change in production)
- Roles: `axiom-user`, `axiom-admin`
- Groups: `team-a`, `team-b`
- Sample users: `alice` / `password` (in `team-a`), `bob` / `password` (in `team-b`), `carol` / `password` (admin)

## Repo layout

```
api/        # FastAPI BFF + API + SQLAlchemy models + Alembic migrations
web/        # React + Vite SPA
keycloak/   # Realm import JSON
docker-compose.yml
.env.example
```

## Development without Docker

```bash
# API
cd api && python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
uvicorn axiom_api.main:app --reload

# Web
cd web && npm install
npm run dev
```
