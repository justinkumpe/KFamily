import pytest


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("PYTHONPATH", "src")


def test_status_ok():
    from app.app import create_app

    app = create_app()
    client = app.test_client()
    resp = client.get("/status.json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
