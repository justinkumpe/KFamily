import pytest


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("PYTHONPATH", "src")


def test_register_then_login(client):
    from app.app import create_app

    app = create_app()
    app.config.update(TESTING=True, SECRET_KEY="test")
    c = app.test_client()

    # register
    rv = c.post(
        "/register",
        data=dict(email="u@example.com", display_name="User", password="secret123"),
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # login
    rv = c.post(
        "/login",
        data=dict(email="u@example.com", password="secret123"),
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # access family (login required)
    rv = c.get("/family")
    assert rv.status_code == 200


def test_users_requires_admin(client):
    from app.app import create_app

    app = create_app()
    app.config.update(TESTING=True, SECRET_KEY="test")
    c = app.test_client()

    # anonymous should be redirected to login
    rv = c.get("/users")
    assert rv.status_code in (301, 302)