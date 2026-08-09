# HELP ME API Service

Initial scaffolding for the modular FastAPI monolith described in `docs/blueprint/architecture-overview.md`.

## Features
- Settings via `pydantic-settings` with env prefix `HELP_ME_`.
- Async SQLAlchemy engine/session manager (`services/api/app/db.py`).
- Base ORM models (Tenant, Case, ReporterHandle) aligned with the core data model.
- Public intake router (`POST /public/tenants/{slug}/cases`) that generates HELP ME case IDs and reporter handles.
- Health endpoint for readiness checks.

## Running Locally
```bash
export HELP_ME_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/safelytold"
export HELP_ME_ENVIRONMENT=development
uvicorn services.api.app.main:app --reload
```

Create tables (or run migrations) with Alembic:

```bash
alembic -c services/api/alembic.ini upgrade head
```

In development the app auto-creates tables (for convenience). For staging/prod use Alembic migrations (to be added).
