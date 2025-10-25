from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, render_template, redirect, url_for, request
from flask_login import LoginManager, current_user, login_required
from flask_wtf import CSRFProtect

from .db import SessionLocal
from .modules.family.routes import family_bp
from .modules.family.relationships import relationships_bp
from .modules.family.tree import tree_bp
from .modules.users.routes import users_bp


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Basic config
    app.config.setdefault("JSON_SORT_KEYS", False)
    app.config.setdefault("APP_STARTED_AT", datetime.utcnow().isoformat() + "Z")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # CSRF and Login
    # Disable CSRF in testing to simplify form posts in unit tests
    if app.config.get("TESTING"):
        app.config["WTF_CSRF_ENABLED"] = False
    # Initialize CSRF protection but will exempt API routes after blueprint registration
    csrf = CSRFProtect(app)
    
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"

    from .modules.users.models import User  # local import to avoid cycle
    from sqlalchemy.orm import selectinload

    @login_manager.user_loader
    def load_user(user_id: str):
        sess = app.session  # type: ignore[attr-defined]
        from sqlalchemy import select
        # Eager-load groups to ensure has_any_group works correctly
        stmt = select(User).where(User.id == int(user_id)).options(selectinload(User.groups))
        return sess.scalar(stmt)

    # DB session per request
    @app.before_request
    def _create_session():  # type: ignore[no-redef]
        app.session = SessionLocal()  # type: ignore[attr-defined]

    @app.teardown_request
    def _shutdown_session(exception: Exception | None):  # type: ignore[no-redef]
        sess = getattr(app, "session", None)
        if sess is not None:
            try:
                if exception is not None:
                    sess.rollback()
                sess.close()
            except Exception as e:
                # Ignore session state errors during teardown
                app.logger.debug(f"Session teardown error (ignored): {e}")

    @app.get("/")
    def index() -> Any:
        return render_template("index.html")

    @app.get("/status.json")
    def status_json() -> Any:
        return jsonify({
            "name": "KFamily",
            "status": "ok",
            "started": app.config["APP_STARTED_AT"],
            "modules": ["users", "family"],
        })

    def require_groups(*groups: str):
        def decorator(fn):
            from functools import wraps

            @wraps(fn)
            def wrapper(*args, **kwargs):
                if not current_user.is_authenticated:
                    return redirect(url_for("auth.login", next=request.path))
                if groups and not current_user.has_any_group(*groups):  # type: ignore[attr-defined]
                    # fallback: show 403 page or flash + redirect
                    return redirect(url_for("index"))
                return fn(*args, **kwargs)

            return wrapper

        return decorator

    @app.get("/users")
    @require_groups("admin", "super-admin")
    def users_page() -> Any:
        return render_template("users.html")

    @app.get("/family")
    @login_required
    def family_page() -> Any:
        return render_template("family.html")

    @app.get("/tree")
    @login_required
    def tree_page() -> Any:
        return render_template("tree.html")

    @app.get("/admin/users")
    @login_required
    def admin_users_page() -> Any:
        # Allow both admins and household parents to access
        # Permissions will be checked per-action in the API
        return render_template("admin/users.html", current_user_id=current_user.id)

    # Register blueprints
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(family_bp, url_prefix="/api/family")
    app.register_blueprint(relationships_bp, url_prefix="/api/relationships")
    app.register_blueprint(tree_bp, url_prefix="/api/tree")

    # Auth blueprint
    from .modules.auth.routes import auth_bp
    app.register_blueprint(auth_bp)
    
    # Exempt API blueprints from CSRF protection (they use session-based auth)
    csrf.exempt(users_bp)
    csrf.exempt(family_bp)
    csrf.exempt(relationships_bp)
    csrf.exempt(tree_bp)

    return app
