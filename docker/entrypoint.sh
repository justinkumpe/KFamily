#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Starting container..."

export PYTHONPATH="/app/src:${PYTHONPATH:-}"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "[entrypoint] ERROR: DATABASE_URL is not set."
  echo "  Example (MariaDB): mysql+pymysql://user:pass@host:3306/dbname?charset=utf8mb4"
  exit 1
fi

# Basic wait for DB readiness using Python + SQLAlchemy (DB-agnostic)
echo "[entrypoint] Waiting for database to become available..."
python - <<'PYCODE'
import os, sys, time
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]
engine = create_engine(url)

deadline = time.time() + 180
last_err = None
while time.time() < deadline:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("DB ready.")
        sys.exit(0)
    except Exception as e:
        last_err = e
        time.sleep(2)

print("DB not ready in time:", last_err)
sys.exit(1)
PYCODE

echo "[entrypoint] Running Alembic migrations..."
alembic upgrade head

echo "[entrypoint] Launching app: $*"
exec "$@"
