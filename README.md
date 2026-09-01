# CRM Platform — Microservices Monorepo

A microservices-based backend platform, currently composed of two independent
FastAPI services. This is an early-stage foundation: the plan is to connect the
services behind a shared entry point, add Celery for background/async work, and
build the core CRM domain logic on top.

## Current status

🚧 **Pre-integration.** Each service currently runs and is tested independently.
They are not yet wired together (no shared gateway, no inter-service auth
validation, no message broker). See [Roadmap](#roadmap) below.

## Services

### `auth_microservice`
Handles authentication, multi-tenant companies, and user/member management.

- **Domain model:** `Company` → `CompanyMember` (with `role`) → `User`,
  plus `CompanyInvite` for onboarding new members.
- **Auth:** JWT access + refresh tokens (`PyJWT`), bcrypt password hashing,
  password-reset flow via short-lived JWT.
- **Roles:** `OWNER`, `DISPATCHER`, `DRIVER`, `ACCOUNTANT`, `VIEWER`
  (role-based endpoint guards via `require_role`).
- **Endpoints:** `/api/v1/auth/*`, `/api/v1/users/*`, `/api/v1/companies/*`.
- **Caching:** Redis, with cache invalidation on every mutating request
  (user, company, member list/detail keys).

### `todo_microservice`
A task/CRM-adjacent service, currently a standalone To-Do CRM skeleton.

- **Domain model:** `Task` (title, description, completion state, deadline).
- **Endpoints:** `/api/v1/tasks/*` — full CRUD.
- **Caching:** Redis, list + detail keys invalidated on create/update/delete.

### Shared stack (both services)
- FastAPI + async SQLAlchemy 2.0 (`asyncpg` in prod, `aiosqlite` in tests)
- Alembic migrations (async-aware `env.py`)
- Redis for response caching
- Structured request logging middleware with `X-Request-ID`
- Pytest + `pytest-asyncio`, `httpx.AsyncClient` against an in-memory SQLite DB
  and a real (flushed-per-test) Redis instance
- Dockerized, orchestrated via the root `docker-compose.yml`

## Repository layout

```
.
├── auth_microservice/
│   ├── app/
│   │   ├── router/        # auth_router, user_router, company_router
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── security.py    # JWT + password hashing
│   │   ├── dependencies.py# get_current_user, require_role
│   │   ├── database.py
│   │   └── redis_client.py
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── alembic.ini
├── todo_microservice/
│   ├── app/
│   │   ├── router/         # task_router
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   └── redis_client.py
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── alembic.ini
└── docker-compose.yml
```

## Getting started

### Prerequisites
- Docker + Docker Compose
- A `.env` file in each service directory (`auth_microservice/.env`,
  `todo_microservice/.env`) — see [Environment variables](#environment-variables)
- A running Redis instance reachable by both services (not yet included in
  `docker-compose.yml` — see Roadmap)

### Run with Docker Compose

```bash
docker compose up --build
```

This starts:
- `auth_db` (Postgres) on host port `5434`
- `auth_app` on host port `8002`
- `todo_db` (Postgres) on host port `5432`
- `todo_app` on host port `8001`

Migrations run automatically on container start (`alembic upgrade head`).

### Run a service locally (without Docker)

```bash
cd auth_microservice        # or todo_microservice
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Run tests

```bash
cd auth_microservice        # or todo_microservice
pytest
```

Tests use an in-memory SQLite database and a real Redis instance (flushed
before/after each test), so `REDIS_NAME`, `REDIS_HOST`, and `REDIS_PORT` must
be set even when running tests.

## Environment variables

Each service reads from its own `.env` file.

| Variable | Used for | Example |
|---|---|---|
| `DATABASE_URL` | full DB connection string (overrides individual `DB_*` vars) | `postgresql+asyncpg://user:pass@host:5432/db` |
| `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` / `DB_NAME` | fallback DB config if `DATABASE_URL` not set | |
| `REDIS_NAME` | Redis URL scheme | `redis` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `SECRET_KEY` *(auth only)* | JWT signing key | — |
| `ALGORITHM` *(auth only)* | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` *(auth only)* | access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` *(auth only)* | refresh token TTL | `7` |

## Roadmap

Near-term plan, in order:

1. **Connect the microservices**
   - Introduce a shared API gateway or direct service-to-service calls
     for the `todo`/CRM service to validate JWTs issued by `auth_microservice`
     (shared `SECRET_KEY`/`ALGORITHM`, or a token-introspection endpoint).
   - Add Redis and a network to `docker-compose.yml` so all services and
     dependencies come up together with one command.
   - Decide on a single external port scheme (avoid host-port collisions,
     e.g. `todo_db` currently binds to `5432`, which collides with a local
     Postgres install).

2. **Add Celery**
   - Introduce a broker (Redis, already present, or RabbitMQ) and a Celery
     worker service per microservice or a shared worker service.
   - Move non-critical side effects off the request path: sending invite/
     reset-password emails (currently just `print()`-ed), cache warmup,
     scheduled/periodic jobs (`celery beat`) for reminders, deadline checks,
     digesting, etc.

3. **Core CRM logic**
   - Expand `todo_microservice` (or a new `crm_microservice`) beyond simple
     tasks into real CRM entities: contacts/leads, deals/pipelines, activity
     history, assignment to `CompanyMember`s and roles.
   - Enforce company-scoped data access (tasks/CRM records should belong to
     a `company_id`, mirroring the auth service's tenancy model).

## Known issues / hardening backlog

Carried over from a security review of the current codebase — worth
addressing before or during the integration work above:

- `accept_invite` attaches an invite to an *existing* user account without
  verifying the requester owns that account (no password/auth check).
- Password-reset tokens are stateless JWTs with no single-use enforcement —
  the same reset link can be replayed until it expires.
- Password reset doesn't revoke previously issued access/refresh tokens.
- `/auth/refresh` picks the first active company membership rather than the
  `company_id` embedded in the refresh token, which can silently switch a
  multi-company user's context.
- `get_current_user` doesn't re-check that the specific `CompanyMemberModel`
  referenced by the token is still active, so a removed member stays
  authorized until their token naturally expires.
- `todo_microservice`'s task list endpoint caches under a hardcoded
  `limit=10:offset=0` key with no actual pagination parameters exposed.

## License

TBD.
