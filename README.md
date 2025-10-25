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

## Automated Scripts

### Relationship Inference (Runs Automatically Every 15 Minutes)

The relationship inference script automatically creates extended family relationships based on existing direct relationships. For example, if Waylon has Justin as father, and Justin has Cindy as mother, the script will automatically create grandmother/grandson relationships.

**The inference service runs automatically** as part of the Docker Compose stack, checking for new relationships every 15 minutes.

**View inference logs:**

```bash
# View recent activity
docker compose logs relationship-inference --tail 50

# Follow logs in real-time
docker compose logs relationship-inference -f
```

**Manually trigger inference (run immediately):**

```bash
docker compose exec relationship-inference python /app/scripts/infer_family_relationships.py
```

**Adjust the interval:**

Edit `docker-compose.yml` and change `sleep 900` to your desired interval (in seconds), then:

```bash
docker compose up -d --force-recreate relationship-inference
```

**Run manually without the service:**

```bash
# Dry run (preview what would be created)
docker compose exec app python /app/scripts/infer_family_relationships.py --dry-run

# Actually create the relationships
docker compose exec app python /app/scripts/infer_family_relationships.py
```

**Disable automatic inference:**

If you want to disable the automatic inference service:

```bash
docker compose stop relationship-inference
```

See [docs/RELATIONSHIP_INFERENCE.md](docs/RELATIONSHIP_INFERENCE.md) for complete documentation including:
- Supported relationship types (grandparents, aunts/uncles, in-laws, cousins, etc.)
- Gender-aware reciprocal relationship creation
- Manual scheduling options (cron, systemd timer)
- Best practices and troubleshooting

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

## Timeline Module

The Timeline module provides a comprehensive event tracking system for user life events.

### Features

- **Auto-Generated Events** — Birth, adoption, and death dates automatically create timeline events
- **Custom Events** — Modules can define their own event types using the template system
- **Visibility Controls** — Events can be public, family, household, parents-only, or private
- **User Detail Pages** — Full-page user profiles with tabbed interface (Overview and Timeline)
- **Inline Editing** — Click-to-edit functionality for user profile fields
- **Extensible Templates** — Module-based template system for defining custom event types

### Timeline Event Templates

The template system allows modules to define custom timeline event types with standardized formatting and validation.

**Built-in Event Types:**

- `birth` — Birth event (auto-generated from birthday field)
- `adoption` — Adoption event (auto-generated from adoption_date field)
- `death` — Death event (auto-generated from death_date field)

**API Endpoints:**

- `GET /api/timeline/templates` — List all available event templates
- `GET /api/timeline/templates/<event_type>` — Get specific template details
- `GET /api/timeline/users/<id>` — Get user's timeline events
- `POST /api/timeline/users/<id>` — Create new timeline event
- `PATCH /api/timeline/<event_id>` — Update timeline event
- `DELETE /api/timeline/<event_id>` — Delete timeline event

**Creating Custom Event Templates:**

See [docs/TIMELINE_TEMPLATES.md](docs/TIMELINE_TEMPLATES.md) for comprehensive documentation on creating custom event templates for your modules.

**Example Usage:**

```python
from app.modules.timeline import TimelineEventTemplate, register_template

class GraduationEventTemplate(TimelineEventTemplate):
    event_type = "graduation"
    module_name = "education"
    display_name = "Graduation"
    icon_class = "bi-mortarboard"
    color_class = "info"
    
    def get_metadata_schema(self):
        return {
            "type": "object",
            "properties": {
                "school": {"type": "string"},
                "degree": {"type": "string"}
            }
        }

register_template(GraduationEventTemplate())
```

### User Detail Pages

Navigate to `/users/<id>` to view comprehensive user information:

- **Overview Tab** — Personal information, contact details, important dates, households, and relationships
- **Timeline Tab** — Chronological display of life events with icons and visibility badges
- **Edit Mode** — Click "Edit" button to enable inline editing of profile fields (permission-based)

**Inline Editing:**

1. Click the "Edit" button (visible only if you have edit permissions)
2. Click on any field value to start editing
3. Make your changes and click "Save" or "Cancel"
4. Click "Done" to exit edit mode

Changes to birth, adoption, or death dates automatically update timeline events.
