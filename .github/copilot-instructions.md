# Copilot Instructions for KFamily

Purpose
- Give AI coding agents fast, accurate context to work productively in this repo.
- Document only what’s observable today; flag unknowns for quick confirmation.

Repository snapshot (as of this doc)
- Top-level files: `README.md` (title only), `KFamily.code-workspace` (single-folder VS Code workspace)
- Branches: default = `main`; integration branch = `dev` (start new work from `dev`)
- No app code yet; no build/test config or CI.

How to work in this repository
- Branching: Create feature branches from `dev`, open PRs back to `dev`. Default branch is `main`.
- PR hygiene: In the PR description, state assumptions (stack, structure), list added files, and how to run/build/test. Keep changes small and scoped.
- Workspace: Use `KFamily.code-workspace`. When adding folders, ensure the workspace still opens cleanly.

Primary stack and conventions (confirmed)
- Language: Python
- ORM/DB: SQLAlchemy (database-agnostic). Use Alembic for migrations.
- Code quality: Black (format), Pylint (lint).
- Packaging/runtime: Dockerized app. Container startup must automatically run DB migrations and any startup scripts.
 - Target database: MariaDB (via SQLAlchemy MySQL dialect). Keep code DB-agnostic.

When adding the first Python code
- Scaffold minimal, conventional structure:
  - `src/` for app code (e.g., `src/app/__init__.py`, `src/app/db.py`, `src/app/models.py`)
  - `migrations/` for Alembic
  - `tests/` for unit tests (pytest)
  - `pyproject.toml` (preferred) or `requirements.txt` with pinned deps
- Dependencies (pin versions): `sqlalchemy`, `alembic`, `pydantic` (if models/schemas), `pytest`, `black`, `pylint`.
- Provide a tiny smoke entrypoint (e.g., `python -m app` or `src/app/__main__.py`) that can start without external services (or stubs).
- Add formatting/lint tasks and a basic test.

Docker and startup behavior
- Include a `Dockerfile` that:
  - Installs Python deps with pinned versions
  - Copies source, sets `PYTHONPATH` for `src/`
  - Runs a startup script/entrypoint that executes Alembic migrations before launching the app
- Include a lightweight `docker/entrypoint.sh` or equivalent that:
  - Waits for DB availability (if needed)
  - Runs `alembic upgrade head`
  - Executes the app process
- Document required env vars: DB URL (e.g., `DATABASE_URL`), app env, ports.
 - Example `DATABASE_URL` for MariaDB (sync): `mysql+pymysql://user:pass@host:3306/dbname?charset=utf8mb4`
 - Deployment: Docker-only (no Kubernetes assumed at this time).

Docs and conventions to follow
- Update `README.md` when adding runnable code with:
  - Quick start: local run (venv) and Docker run
  - Project layout
  - Environment variables (e.g., `DATABASE_URL`) and secrets handling
  - Migrations workflow (local: `alembic revision --autogenerate`, `alembic upgrade head`; Docker: auto-run on start)

Quality and CI
- Add a basic GitHub Actions workflow when code exists to run:
  - Black (check) and Pylint
  - Pytest (unit tests)
  - Optional: build Docker image to validate `Dockerfile`

Examples to mirror in this repo
- VS Code: Keep `KFamily.code-workspace` updated when adding folders so contributors can open the workspace cleanly.
- Branching: Work on `dev` then PR back to `dev` (observed presence of `dev` suggests it’s the integration branch), then maintainers can promote to `main`.

Unknowns to confirm quickly
- Target database vendor(s) for dev/prod (e.g., Postgres, MySQL, SQLite)
- Deployment environment (Docker runtime only? Or orchestrator like ECS/Kubernetes?)
- Any required external integrations (APIs, cloud services) and secrets management approach

File reference
- `README.md` — project title (expand as you add functionality)
- `KFamily.code-workspace` — VS Code workspace definition
 - `.github/workflows/` — add CI once code exists
 - `Dockerfile`, `docker/entrypoint.sh` — container runtime and auto-migrations
 - `alembic.ini`, `migrations/` — Alembic configuration and migration history

Contact/feedback
- If something here is inaccurate or missing, update this file in the same PR where you introduce new structure so future agents have the latest truth.
