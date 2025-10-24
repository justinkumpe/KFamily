import importlib


def test_smoke_engine_creation(monkeypatch):
    # Use SQLite memory for test isolation; app remains DB-agnostic
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    mod = importlib.import_module("app.db")
    engine = mod.get_engine()
    with engine.connect() as conn:
        _ = conn.execute(mod.text("SELECT 1")).scalar_one_or_none() if hasattr(mod, "text") else 1
    assert engine is not None
