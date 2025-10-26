from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL_ENV = "DATABASE_URL"


def _get_database_url() -> str:
    url = os.getenv(DATABASE_URL_ENV)
    if not url:
        # Example MariaDB DSN: mysql+pymysql://user:pass@host:3306/dbname?charset=utf8mb4
        raise RuntimeError(
            f"{DATABASE_URL_ENV} is not set. Expected a SQLAlchemy URL (e.g., MariaDB: "
            "mysql+pymysql://user:pass@host:3306/dbname?charset=utf8mb4)."
        )
    return url


def get_engine(echo: bool | None = None):
    """Create and return a SQLAlchemy engine using env DATABASE_URL.

    Keep DB-agnostic by relying on SQLAlchemy URL dialect.
    Configures connection pool to handle concurrent requests.
    """

    url = _get_database_url()
    return create_engine(
        url, 
        echo=bool(echo),
        pool_size=10,  # Increased from default 5
        max_overflow=20,  # Increased from default 10
        pool_pre_ping=True,  # Verify connections are alive before using
        pool_recycle=3600  # Recycle connections after 1 hour
    )


Base = declarative_base()


def _session_factory():
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


SessionLocal = _session_factory()


@contextmanager
def session_scope() -> Iterator:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
