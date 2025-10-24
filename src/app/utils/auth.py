from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable

from flask import jsonify, current_app
from flask_login import current_user


def api_login_required(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "authentication required"}), 401
        return fn(*args, **kwargs)

    return wrapper


def api_require_groups(groups: Iterable[str]):
    required = tuple(groups)

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "authentication required"}), 401
            # type: ignore[attr-defined]
            if required and not current_user.has_any_group(*required):
                return jsonify({"error": "forbidden", "required_groups": list(required)}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def api_allow_household_parent(fn: Callable):
    """
    Allow access if user is:
    1. Admin/super-admin, OR
    2. A parent in the same household as the target user
    
    Expects target_user_id or user_id in the route kwargs.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "authentication required"}), 401
        
        # Debug: Log user groups
        user_groups = [g.name for g in current_user.groups] if hasattr(current_user, 'groups') else []
        current_app.logger.info(f"User {current_user.id} groups: {user_groups}")
        
        # Allow admins full access
        has_admin = current_user.has_any_group("admin", "super-admin")
        current_app.logger.info(f"User {current_user.id} has_admin: {has_admin}")
        
        if has_admin:
            return fn(*args, **kwargs)
        
        # Check if user is a household parent of the target user
        target_user_id = kwargs.get("user_id") or kwargs.get("target_user_id")
        if target_user_id:
            can_edit = current_user.can_edit_household_member(target_user_id)
            current_app.logger.info(f"User {current_user.id} can_edit {target_user_id}: {can_edit}")
            if can_edit:
                return fn(*args, **kwargs)
        
        return jsonify({"error": "forbidden", "message": "Must be admin or household parent"}), 403

    return wrapper
