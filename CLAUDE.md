# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo shape

Three top-level apps wired together by `docker-compose.yml`:

- `api/` — Python 3.12 / FastAPI BFF + REST API + SQLAlchemy 2.x models + Alembic migrations. Package lives at `api/src/axiom_api/`.
- `web/` — Vite + React 18 + TypeScript + MUI v6 SPA.
- `keycloak/realm-axiom.json` — auto-imported realm with the `axiom-bff` confidential client, `axiom-user`/`axiom-admin` roles, `team-a`/`team-b` groups, and sample users (`alice`, `bob`, `carol`, all password `password`).

## Common commands

### Full stack (preferred)

```bash
cp .env.example .env       # first time only
docker compose up --build
```

URLs: web `http://localhost:5173`, API + `/docs` `http://localhost:8000`, Keycloak admin `http://localhost:8080` (admin/admin).

### API (run from `api/`)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .[dev]
alembic upgrade head
uvicorn axiom_api.main:app --reload

pytest                                # all tests
pytest tests/test_smoke.py::test_name # single test
ruff check . && ruff format .
mypy src
alembic revision --autogenerate -m "msg"   # new migration
```

`pyproject.toml` sets `asyncio_mode = "auto"`, line length 100, ruff lint rules `E,F,W,I,UP,B,SIM`.

### Web (run from `web/`)

```bash
npm install
npm run dev      # vite on 0.0.0.0:5173
npm run build    # tsc -b && vite build
npm run lint     # eslint .ts/.tsx
npm test         # vitest run
```

## Architecture: the BFF pattern (critical)

The SPA **never** sees OIDC tokens. Every browser request is cookie-authenticated; the API holds the tokens.

1. Browser hits `/api/auth/login` → 302 to Keycloak with PKCE.
2. Keycloak → `/api/auth/callback` → API exchanges code, stores `id_token`/`access_token`/`refresh_token` **encrypted at rest** in the `oidc_sessions` table, sets an httponly `axiom_sid` cookie, then redirects back to the SPA.
3. SPA calls `/api/...` with `credentials: 'include'`. `deps.current_user` resolves the cookie → DB session → `CurrentUser` (sub, username, email, Keycloak `groups`, `roles`, `is_admin`).
4. `/api/auth/logout` deletes the DB session, clears the cookie, and returns the Keycloak end-session URL for the SPA to redirect to.

Implementation entry points:

- `api/src/axiom_api/routers/auth.py` — login/callback/me/logout
- `api/src/axiom_api/services/oidc.py` — Keycloak/Authlib calls, PKCE
- `api/src/axiom_api/services/session_store.py` — create/get/delete sessions
- `api/src/axiom_api/services/crypto.py` — Fernet encryption keyed by `SESSION_ENCRYPTION_KEY` (32-byte urlsafe base64)
- `api/src/axiom_api/deps.py` — `CurrentUserDep`, `AdminDep`, `DbDep`
- `web/src/api/client.ts` — `api()` helper (always `credentials: 'include'`), `loginRedirect`, `logout`
- `web/src/auth/AuthGate.tsx` — gates routes on `/api/auth/me`

Implications when editing:

- Never plumb access tokens to the SPA. Anything the SPA needs from claims goes through `/api/auth/me` or a server-rendered response.
- `_oidc_state` in `routers/auth.py` is in-process (dev only). Don't rely on it for multi-instance prod.
- All cookies and CORS are scoped to `WEB_PUBLIC_URL`; cross-origin work needs config changes, not ad-hoc headers.

## Architecture: tests, events, metadata, ACLs

Domain models live in `api/src/axiom_api/models/`:

- **Test** (top-level container) → has many **Event**s. Both store metadata as JSONB keyed by `MetadataField.id`.
- **MetadataField** is a global data dictionary entry. Each field has a `data_type` (string/number/bool/date/enum), a `status` (`active` / `on_the_fly`), and an optional `namespace_group_id`. A `null` namespace means **shared**; a non-null namespace restricts the field to members of that Keycloak group.
- **TestFieldBinding** declares that a field is `REQUIRED` or `OPTIONAL` for a test, either at the test level or per-event (`BindingApplies.TEST` / `EVENT`). Optional bindings can be promoted to required; on-the-fly fields can be promoted into the dictionary.
- **TestAcl** binds Keycloak groups to a test with `READ` / `WRITE` / `ADMIN` permissions.
- All domain rows use `TimestampedMixin` (UUID PK, `created_at/by`, `updated_at/by`, soft-delete via `deleted_at`). Every create/update/delete writes an `AuditLog` row.

### Two service modules do the heavy lifting — read these before changing domain code

- `services/authz.py` — `require_read(db, user, test_id)` / `require_write(...)` / `accessible_test_ids(...)`. Admin short-circuits to "all". Caller's group keys = `{*user.groups, *user.group_ids}` (we match against both Keycloak group names and UUIDs because the JWT and the admin API surface them differently).
- `services/metadata.py` — `validate_event_metadata(...)` coerces values to field types, **silently drops** writes to namespaced fields the caller can't see, and enforces required bindings only for namespaces the caller belongs to. `filter_event_metadata_for_caller(...)` is the read-side equivalent. `upsert_on_the_fly_fields(...)` creates new dictionary entries with `status=ON_THE_FLY`.

The namespace-filter behavior is intentional: team-a and team-b can share an event without leaking each other's fields. Don't "fix" this by raising 403 — silently dropping is the contract.

## Architecture: the frontend

- `main.tsx` wires `ThemeProvider` → `QueryClientProvider` (TanStack Query, `staleTime: 5000`, no focus refetch) → `BrowserRouter` → `AuthGate` → `AppShell` → routes.
- Routes (`web/src/routes/`): `TestsList`, `TestDetail`, `EventGrid`, `EventForm`, `TestSettings`, `Dictionary`, `Admin`, `Audit`.
- All HTTP goes through `api()` in `web/src/api/client.ts` — never call `fetch` directly, because the helper centralizes the `credentials: 'include'` and error shape.
- Vite proxies `/api` to `VITE_API_BASE_URL` (defaults to `http://api:8000` inside Compose, `http://localhost:8000` for non-Docker dev). The path prefix is always `/api`, both in Compose and in standalone dev — relative URLs only.

## Environment & gotchas

- `SESSION_ENCRYPTION_KEY` must be a 32-byte urlsafe-base64 string. Generate: `python -c "import secrets,base64;print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"`. Rotating it invalidates every existing session.
- `KEYCLOAK_URL` is the **internal** URL the API uses to talk to Keycloak (Compose: `http://keycloak:8080`). `KEYCLOAK_PUBLIC_URL` is the URL the browser follows during redirects (`http://localhost:8080`). These must differ in Compose; conflating them breaks login.
- `VITE_API_BASE_URL` likewise: `http://api:8000` inside Compose, `http://localhost:8000` outside. Recent fix `c6704f4` exists because the dev proxy was misaimed at `localhost`.
- The API Dockerfile copies source before `pip install -e .` — preserve that order if editing (`f6a3105`).
- Alembic discovers models via `axiom_api.models` `__init__` (which imports every model module). New models must be imported there or autogenerate won't see them.
