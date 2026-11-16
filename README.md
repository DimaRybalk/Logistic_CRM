# Logistics CRM Platform — Microservices Monorepo

A multi-tenant backend platform for freight forwarding companies. It is built as three independent services behind a single Nginx gateway, with stateless JWT authentication shared between them.

## Architecture

```
                    ┌────────────────────────┐
   Client  ───────► │  Nginx gateway (:80)   │
                    └───────────┬────────────┘
        /api/auth/   │   /api/todos/   │   /api/crm/, /admin/
                     ▼                 ▼                 ▼
            ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
            │ auth_app       │ │ todo_app       │ │ crm_app        │
            │ FastAPI        │ │ FastAPI        │ │ Django + DRF   │
            └───┬───────┬────┘ └───┬───────┬────┘ └───────┬────────┘
                │       │          │       │              │
           Postgres   Redis    Postgres   Redis        Postgres
                                          │
                              Celery worker + beat ──► Mailpit (SMTP)
```

| Service | Stack | Purpose |
|---|---|---|
| `auth_microservice` | FastAPI, async SQLAlchemy 2.0, Alembic, Redis | Registration, login, JWT, companies, members, invites |
| `todo_microservice` | FastAPI, async SQLAlchemy 2.0, Alembic, Redis, Celery | Personal task list with deadline reminders |
| `crm_microservice` | Django 5, Django REST Framework, drf-spectacular | Core logistics CRM: counterparties, directory, orders |
| `nginx` | Nginx | Single entry point, routes requests to services |

### How authentication works

1. A user logs in via `auth_microservice` and receives an **access** and a **refresh** JWT.
2. The token payload contains `sub` (user id), `company_id` and `role`.
3. `todo_microservice` and `crm_microservice` **validate the JWT themselves** (stateless, shared secret) — they never call the auth service.
4. Every record in the CRM and Todo services carries a `company_id`, and every query is filtered by the `company_id` from the token. This gives tenant isolation.

### Roles

`OWNER`, `FORWARDER`, `DISPATCHER`, `DRIVER`, `ACCOUNTANT`, `VIEWER`

CRM access rules:

| Resource | OWNER | FORWARDER | VIEWER | Others |
|---|---|---|---|---|
| Counterparties, Contacts, Banking details | full | full | no access | no access |
| Locations, Cargos, Vehicles, Trailers, Orders | full | full | read-only | no access |

Additionally, a `FORWARDER` can only modify orders they are responsible for, cannot delete, and cannot edit orders with status `CLOSED`.

## Services in detail

### `auth_microservice`

- **Domain:** `Company` → `CompanyMember` (with `role`) → `User`, plus `CompanyInvite`.
- **Auth:** JWT access + refresh tokens (PyJWT), bcrypt hashing, password reset via short-lived JWT, logout via a Redis token blacklist.
- **Endpoints:** `/api/v1/auth/*`, `/api/v1/users/*`, `/api/v1/companies/*`
- **Caching:** Redis, invalidated on every mutating request.

### `todo_microservice`

- **Domain:** `Task` (title, description, completion, deadline), scoped by `user_id` and `company_id`.
- **Endpoints:** `/api/v1/tasks/*` — full CRUD.
- **Caching:** Redis list + detail keys, invalidated on create/update/delete.
- **Background jobs (Celery, Redis broker):**
  - email notification when a task is created,
  - every 5 minutes: reminders for deadlines within the next 30 minutes,
  - every hour: cleanup of tasks completed more than 48 hours ago.
- Emails are sent via SMTP to **Mailpit** (a local mail catcher).

### `crm_microservice`

Apps: `clients`, `directory`, `orders`. All data is scoped by `company_id`.

| Entity | Description |
|---|---|
| `Counterparty` | Client and/or carrier company |
| `Location`, `BankingDetail`, `Contact` | Addresses, bank details (IBAN is normalized), people (drivers, brokers, etc.) |
| `Cargo` / `CargoItem` | Shipment with items; ADR class, temperature control, auto-calculated volume |
| `Vehicle`, `Trailer` | Carrier fleet; plate/VIN validation |
| `Order` / `OrderStop` | Transport order with ordered route stops, prices in two currencies, payment terms, border crossing, status workflow, calculated margin |

- **Endpoints** (prefix `/api/crm/v1/`): `counterparties`, `locations`, `banking-details`, `contacts`, `cargos`, `vehicles`, `trailers`, `orders` — with filtering, search and ordering.
- **API docs:** Swagger UI at `/api/crm/docs/`, OpenAPI schema at `/api/crm/schema/`.
- **Admin:** Django admin at `/admin/`.
- Related objects sent by id (`client_id`, `carrier_id`, `vehicle_id`, …) are validated to belong to the same company (`CompanyScopedPKField`).

## Repository layout

```
.
├── auth_microservice/
│   ├── app/            # main, models, schemas, security, dependencies, router/
│   ├── alembic/
│   └── tests/
├── todo_microservice/
│   ├── app/            # main, models, schemas, auth, celery_app, celery_tasks, router/
│   ├── alembic/
│   └── tests/
├── crm_microservice/
│   ├── core/           # settings/, urls, authentication, permissions, fields, factories
│   ├── clients/
│   ├── directory/      # models, choices, serializers, views, tests/
│   └── orders/
├── nginx/nginx.conf
└── docker-compose.yml
```

## Getting started

### Prerequisites

- Docker + Docker Compose
- A `.env` file in each service directory: `auth_microservice/.env`, `todo_microservice/.env`, `crm_microservice/.env`

### Run everything

```bash
docker compose up --build
```

This starts the gateway, three Postgres databases, two Redis instances, the three application services, the Celery worker and beat, and Mailpit. Migrations run automatically on start.

| What | URL |
|---|---|
| Gateway (all APIs) | `http://localhost` |
| Auth API | `http://localhost/api/auth/` |
| Todo API | `http://localhost/api/todos/` |
| CRM API | `http://localhost/api/crm/v1/` |
| CRM Swagger | `http://localhost/api/crm/docs/` |
| Django admin | `http://localhost/admin/` |
| Mailpit (caught emails) | `http://localhost:8025` |

Databases and Redis are not exposed on the host; only Nginx (`80`) and Mailpit (`8025`) are.

### Run tests

**Auth and Todo** (SQLite in memory + a real Redis, flushed per test):

```bash
cd auth_microservice      # or todo_microservice
pip install -r requirements.txt
pytest
```

`REDIS_NAME`, `REDIS_HOST` and `REDIS_PORT` must be set. Auth also needs `SECRET_KEY`.

**CRM** (pytest-django + factory_boy, PostgreSQL):

```bash
cd crm_microservice
pip install -r requirements.txt
pytest
```

The database variables and `JWT_SECRET_KEY` / `JWT_ALGORITHM` must be set.

## Environment variables

| Variable | Service | Purpose |
|---|---|---|
| `DATABASE_URL` or `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | auth, todo | Database connection |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | crm | Database connection |
| `REDIS_NAME`, `REDIS_HOST`, `REDIS_PORT` | auth, todo | Redis connection (`redis`, host, `6379`) |
| `SECRET_KEY`, `ALGORITHM` | auth, todo | JWT signing key and algorithm (must match between them) |
| `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` | auth | Token lifetimes (default 30 min / 7 days) |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM` | crm | Must equal auth's `SECRET_KEY` / `ALGORITHM` |
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | crm | Django settings |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM` | todo | Email sending (point to Mailpit) |

## Roadmap

- Event-driven communication between services (RabbitMQ). A publisher stub exists in `auth_microservice/app/rabbitmq.py`, but it is **not wired in yet**.
- Real email sending for invites and password reset (currently printed to logs).
- Expand `todo_microservice` / CRM with leads, deals and activity history.
- CI pipeline (tests + flake8) and a production Django settings file.

## Known issues / hardening backlog

- `accept_invite` attaches an invite to an *existing* user without verifying that the requester owns that account.
- Password-reset tokens are stateless and can be replayed until they expire; a reset does not revoke existing tokens.
- `/auth/refresh` picks the first active membership instead of the `company_id` stored in the refresh token.
- `get_current_user` does not re-check that the member referenced by the token is still active.
- Token revocation (logout blacklist) exists only in the auth service; Todo and CRM do not check it.
- Todo task list is cached under a fixed `limit=10:offset=0` key and has no real pagination.

## License

TBD.
