# KFamily

Minimal Python scaffold with SQLAlchemy + Alembic, Dockerized runtime, and CI.

## Quick start (local)

1. Create and activate a virtual environment.

2. Install deps:

- `pip install -r requirements.txt`
- `pip install -r requirements-dev.txt`

1. Set env and run a smoke check:

- `export DATABASE_URL=sqlite+pysqlite:///:memory:`
- `export PYTHONPATH=src`
- `python -m app`

Run tests:

- `pytest`

Format/lint:

- `black .`
- `pylint src`

## Quick start (Docker)

Build image and run (expects MariaDB URL):

Environment:

- `DATABASE_URL` (e.g., `mysql+pymysql://user:pass@host:3306/dbname?charset=utf8mb4`)

Container behavior:

- Entry point waits for DB, runs `alembic upgrade head`, then starts the app (`python -m app`).

Port mapping:

- Default Flask server listens on 0.0.0.0:8000; map with `-p 8000:8000` when running.

## Command-line (user management)

Commands are provided via a small CLI module. Ensure the database is reachable (set `DATABASE_URL`).

Local (venv):

- `export DATABASE_URL=...`
- `export PYTHONPATH=src`
- `python -m app.cli seed-groups`
- `python -m app.cli create-user you@example.com "Your Name" SuperSecret`
- `python -m app.cli promote-admin you@example.com`
- Or one-shot: `python -m app.cli create-admin you@example.com "Your Name" SuperSecret`

Docker Compose (runs the command inside the app container):

- `docker compose run --rm app python -m app.cli seed-groups`
- `docker compose run --rm app python -m app.cli create-admin admin@example.com "Admin" SuperSecret`

## docker-compose (MariaDB + App)

Start both services:

- `docker compose up --build`

App will be available at <http://localhost:8000>

UI pages:

- `/` — Home
- `/users` — Manage Users
- `/family` — Family module

## Project layout

- `src/app/` — app code
  - `db.py` — SQLAlchemy engine/session
  - `models.py` — SQLAlchemy models
  - `__main__.py` — app entrypoint (smoke)
- `migrations/` — Alembic config and migration history
- `docker/entrypoint.sh` — container startup script (wait + migrate + run)
- `Dockerfile` — container image
- `.github/workflows/ci.yml` — CI for Black, Pylint, Pytest

## Migrations workflow

Local dev:

- `export DATABASE_URL=...`
- `export PYTHONPATH=src`  # ensure Alembic can import `src.app` models
- Create migration: `alembic revision --autogenerate -m "msg"`
- Apply migration: `alembic upgrade head`

Docker:

- Migrations run automatically on container start.

## Authentication

- The app uses Flask-Login and Flask-WTF (CSRF enabled). Set `SECRET_KEY` for session/CSRF security.
- Register at `/register`, then login at `/login`.
- `/family` requires login.
- `/users` requires group membership: `admin` or `super-admin`.
- Default groups can be created via `POST /api/users/seed-groups` or by DB inserts.

## Authorization

- HTML pages
  - `/` — Home dashboard with system overview
  - `/family` — Family management (login required)
  - `/users` — User listing (requires `admin` or `super-admin`)
  - `/admin/users` — Complete user management UI with CRUD operations (requires `admin` or `super-admin`)

- API endpoints
  - `/api/users` (GET/POST) — List/create users (`admin` or `super-admin`)
  - `/api/users/<id>` (PATCH/DELETE) — Update/delete user (`admin` or `super-admin`)
  - `/api/users/<id>/groups` (POST/DELETE) — Manage user groups (`admin` or `super-admin`)
  - `/api/users/groups` (GET) — List all groups (`admin` or `super-admin`)
  - `/api/family/households` (GET) — List households (login required)
  - `/api/family/households` (POST) — Create household (`family-editor`, `family-admin`, `admin`, or `super-admin`)
  - `/api/family/households/<id>/persons` (POST) — Add person (`family-editor`, `family-admin`, `admin`, or `super-admin`)

## Admin Features

The `/admin/users` page provides a complete user management interface:

- **Dashboard Statistics** — View total users, groups, and admin count at a glance
- **Create Users** — Add new users with email, display name, and password
- **Edit Users** — Update user information and reset passwords
- **Delete Users** — Remove users from the system
- **Group Management** — Add/remove groups from users with visual toggle interface
- **Custom Groups** — Create new groups on-the-fly
- **Modern UI** — Card-based layout with animations, icons, and gradient styling

## UI Features

- **Modern Design** — Gradient backgrounds, smooth animations, and Bootstrap Icons
- **Responsive Layout** — Works on desktop, tablet, and mobile devices
- **Interactive Cards** — Hover effects and visual feedback
- **Real-time Updates** — Automatic refresh after CRUD operations
- **Toast Notifications** — Success/error messages with auto-dismiss
- **Color-coded Badges** — Groups displayed with role-specific colors

Grant roles

- Seed groups once: `POST /api/users/seed-groups` or via CLI
- Use `/admin/users` UI to add/remove groups visually
- Or use the CLI: `python -m app.cli add-group user@example.com admin`
