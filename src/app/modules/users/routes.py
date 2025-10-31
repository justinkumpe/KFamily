from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request, render_template
from sqlalchemy import select

from .models import User, Group, INITIAL_GROUPS
from ..family.models import UserRelationship
from ..family.relationships import get_reciprocal_relationship
from ...utils.auth import api_require_groups, api_allow_household_parent, api_login_required


users_bp = Blueprint("users", __name__)


@users_bp.post("/seed-groups")
def seed_groups():
    sess = g.db_session
    existing = {grp.name for grp in sess.scalars(select(Group)).all()}
    created = []
    for name in INITIAL_GROUPS:
        if name not in existing:
            grp = Group(name=name, description=name)
            sess.add(grp)
            created.append(name)
    sess.commit()
    return jsonify({"created": created, "skipped": list(existing & set(INITIAL_GROUPS))})


@users_bp.get("/admin-page")
@api_require_groups(["admin", "super-admin"])
def admin_users_page_api():
    # Serve template through a non-API route in app.py
    return render_template("admin/users.html")


@users_bp.get("")
@api_login_required
def list_users():
    """List users visible to the current user."""
    from flask_login import current_user
    sess = g.db_session
    
    all_users = sess.scalars(select(User)).all()
    
    # Filter to only users that current user can view
    if current_user.has_any_group("admin", "super-admin"):
        visible_users = all_users
    else:
        visible_users = [u for u in all_users if current_user.can_view_user(u.id)]
    
    return jsonify([
        {
            "id": u.id,
            "email": u.email,
            "display_name": u.display_name,
            "groups": [g.name for g in u.groups] if current_user.has_any_group("admin", "super-admin") else [],
            "first_name": u.first_name,
            "middle_name": u.middle_name,
            "last_name": u.last_name,
            "phone": u.phone,
            "address": u.address,
            "birthday": u.birthday.isoformat() if u.birthday else None,
            "death_date": u.death_date.isoformat() if u.death_date else None,
            "adoption_date": u.adoption_date.isoformat() if u.adoption_date else None,
            "sex": u.sex,
            "gender": u.gender,
            "notes": u.notes,
            "age": u.age,
        }
        for u in visible_users
    ])


@users_bp.post("")
@api_require_groups(["admin", "super-admin"])
def create_user():
    data = request.get_json(force=True)
    
    # Determine if this is a record-only user
    has_email = bool(data.get("email"))
    has_password = bool(data.get("password"))
    is_record_only = not (has_email and has_password)
    
    # If record-only, require at least first_name and last_name for identification
    if is_record_only:
        if not data.get("first_name") or not data.get("last_name"):
            return jsonify({"error": "Record-only users must have first_name and last_name"}), 400
    
    # Create display_name
    if data.get("display_name"):
        display_name = data["display_name"]
    elif has_email:
        display_name = data["email"].split("@")[0]
    else:
        # For record-only users, use first + last name
        display_name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
    
    # Helper to convert empty strings to None for optional fields
    def clean_optional(value):
        return value if value and value.strip() else None
    
    user = User(
        email=clean_optional(data.get("email")),
        display_name=display_name,
        password_hash=None,
        is_record_only=is_record_only,
        first_name=clean_optional(data.get("first_name")),
        middle_name=clean_optional(data.get("middle_name")),
        last_name=clean_optional(data.get("last_name")),
        phone=clean_optional(data.get("phone")),
        address=clean_optional(data.get("address")),
        birthday=clean_optional(data.get("birthday")),
        death_date=clean_optional(data.get("death_date")),
        adoption_date=clean_optional(data.get("adoption_date")),
        sex=clean_optional(data.get("sex")),
        gender=clean_optional(data.get("gender")),
        notes=clean_optional(data.get("notes")),
    )
    if has_password:
        user.set_password(data["password"])
    g.db_session.add(user)
    g.db_session.commit()
    
    # Sync timeline events for life dates (birth, adoption, death)
    from app.modules.timeline.helpers import sync_user_life_events
    sync_user_life_events(user, g.db_session)
    g.db_session.commit()
    
    return jsonify({
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "is_record_only": user.is_record_only
    }), 201


@users_bp.post("/<int:user_id>/groups")
@api_require_groups(["admin", "super-admin"])
def add_user_group(user_id: int):
    data = request.get_json(force=True)
    name = data.get("name")
    if not name:
        return jsonify({"error": "group name required"}), 400
    sess = g.db_session
    user = sess.get(User, user_id)
    if not user:
        return jsonify({"error": "not found"}), 404
    grp = sess.scalar(select(Group).where(Group.name == name))
    if not grp:
        grp = Group(name=name, description=name)
        sess.add(grp)
        sess.flush()
    if grp not in user.groups:
        user.groups.append(grp)
    sess.commit()
    return jsonify({"ok": True})


@users_bp.delete("/<int:user_id>/groups")
@api_require_groups(["admin", "super-admin"])
def remove_user_group(user_id: int):
    data = request.get_json(force=True)
    name = data.get("name")
    if not name:
        return jsonify({"error": "group name required"}), 400
    sess = g.db_session
    user = sess.get(User, user_id)
    if not user:
        return jsonify({"error": "not found"}), 404
    grp = next((g for g in user.groups if g.name == name), None)
    if grp:
        user.groups.remove(grp)
        sess.commit()
    return jsonify({"ok": True})


@users_bp.patch("/<int:user_id>")
@api_allow_household_parent
def update_user(user_id: int):
    data = request.get_json(force=True)
    sess = g.db_session
    user = sess.get(User, user_id)
    if not user:
        return jsonify({"error": "not found"}), 404
    
    # Track if sex changed (to update reciprocal relationships)
    old_sex = user.sex
    sex_changed = False
    
    # Helper to convert empty strings to None
    def clean_optional(value):
        return value if value and str(value).strip() else None
    
    if "email" in data:
        user.email = clean_optional(data["email"])
    if "display_name" in data:
        user.display_name = data["display_name"]
    if "password" in data and data["password"]:
        user.set_password(data["password"])
    
    # Re-check validation after field updates, before committing
    # Note: password won't be cleared unless explicitly set to None, so we check current state
    
    # Update family tree fields
    if "first_name" in data:
        user.first_name = clean_optional(data["first_name"])
    if "middle_name" in data:
        user.middle_name = clean_optional(data["middle_name"])
    if "last_name" in data:
        user.last_name = clean_optional(data["last_name"])
    if "phone" in data:
        user.phone = clean_optional(data["phone"])
    if "address" in data:
        user.address = clean_optional(data["address"])
    if "birthday" in data:
        user.birthday = clean_optional(data["birthday"])
    if "death_date" in data:
        user.death_date = clean_optional(data["death_date"])
    if "adoption_date" in data:
        user.adoption_date = clean_optional(data["adoption_date"])
    if "sex" in data:
        new_sex = clean_optional(data["sex"])
        if new_sex != old_sex:
            sex_changed = True
        user.sex = new_sex
    if "gender" in data:
        user.gender = clean_optional(data["gender"])
    if "notes" in data:
        user.notes = clean_optional(data["notes"])
    
    # Update is_record_only flag based on final email and password state
    has_email = user.email is not None and user.email.strip()
    has_password = user.password_hash is not None
    user.is_record_only = not (has_email and has_password)
    
    # If converting to record-only, require first and last name
    if user.is_record_only:
        if not user.first_name or not user.last_name:
            return jsonify({"error": "Record-only users must have first_name and last_name"}), 400
    
    sess.commit()
    
    # Sync timeline events for life dates (birth, adoption, death)
    from app.modules.timeline.helpers import sync_user_life_events
    sync_user_life_events(user, sess)
    sess.commit()
    
    # If sex changed, update all reciprocal relationships
    if sex_changed:
        # Update reciprocals for outgoing relationships
        outgoing_rels = sess.scalars(
            select(UserRelationship).where(UserRelationship.user_id == user_id)
        ).all()
        
        for rel in outgoing_rels:
            related_user = sess.get(User, rel.related_user_id)
            if not related_user:
                continue
            
            # Determine correct reciprocal based on relationship type
            if rel.relationship_type in ["son", "daughter", "child"]:
                correct_reciprocal = get_reciprocal_relationship(rel.relationship_type, related_user.sex)
            elif rel.relationship_type in ["father", "mother", "parent"]:
                correct_reciprocal = get_reciprocal_relationship(rel.relationship_type, related_user.sex)
            elif rel.relationship_type in ["brother", "sister", "sibling"]:
                correct_reciprocal = get_reciprocal_relationship(rel.relationship_type, user.sex)
            else:
                continue
            
            # Find and update reciprocal
            reciprocal = sess.scalar(
                select(UserRelationship).where(
                    UserRelationship.user_id == rel.related_user_id,
                    UserRelationship.related_user_id == user_id
                )
            )
            
            if reciprocal and reciprocal.relationship_type != correct_reciprocal:
                reciprocal.relationship_type = correct_reciprocal
        
        # Update reciprocals for incoming relationships
        incoming_rels = sess.scalars(
            select(UserRelationship).where(UserRelationship.related_user_id == user_id)
        ).all()
        
        for rel in incoming_rels:
            primary_user = sess.get(User, rel.user_id)
            if not primary_user:
                continue
            
            if rel.relationship_type in ["son", "daughter", "child"]:
                correct_reciprocal = get_reciprocal_relationship(rel.relationship_type, user.sex)
            elif rel.relationship_type in ["father", "mother", "parent"]:
                correct_reciprocal = get_reciprocal_relationship(rel.relationship_type, user.sex)
            elif rel.relationship_type in ["brother", "sister", "sibling"]:
                correct_reciprocal = get_reciprocal_relationship(rel.relationship_type, primary_user.sex)
            else:
                continue
            
            # Find and update reciprocal
            reciprocal = sess.scalar(
                select(UserRelationship).where(
                    UserRelationship.user_id == user_id,
                    UserRelationship.related_user_id == rel.user_id
                )
            )
            
            if reciprocal and reciprocal.relationship_type != correct_reciprocal:
                reciprocal.relationship_type = correct_reciprocal
        
        sess.commit()
    
    return jsonify({"id": user.id, "email": user.email, "display_name": user.display_name})


@users_bp.delete("/<int:user_id>")
@api_require_groups(["admin", "super-admin"])
def delete_user(user_id: int):
    sess = g.db_session
    user = sess.get(User, user_id)
    if not user:
        return jsonify({"error": "not found"}), 404
    sess.delete(user)
    sess.commit()
    return jsonify({"ok": True})


@users_bp.get("/<int:user_id>/can-edit")
@api_login_required
def can_edit_user(user_id: int):
    """Check if the current user can edit the specified user."""
    from flask import g
    from flask_login import current_user
    from sqlalchemy.orm import selectinload
    from ..family.models import HouseholdMember, Household
    
    # Get a fresh copy of the current user from the database with relationships loaded
    # This avoids session issues with the cached current_user object
    # Use request-local g.db_session to avoid concurrent session access
    
    # Load the user fresh with necessary relationships for permission checks
    # Use selectinload (separate queries) to avoid complex joins and session issues
    stmt = (
        select(User)
        .where(User.id == current_user.id)
        .options(
            selectinload(User.groups),
            selectinload(User.family_relationships),
            selectinload(User.household_memberships).selectinload(HouseholdMember.household).selectinload(Household.members)
        )
    )
    
    fresh_user = g.db_session.scalar(stmt)
    
    if not fresh_user:
        return jsonify({"can_edit": False, "reason": None})
    
    # Check permissions using the fresh user object
    can_edit = fresh_user.can_edit_user(user_id)
    
    # Determine reason
    if can_edit:
        if fresh_user.id == user_id:
            reason = "self"
        elif fresh_user.has_any_group("admin", "super-admin"):
            reason = "admin"
        elif fresh_user.can_edit_household_member(user_id):
            reason = "household_admin"
        else:
            reason = "parent"
    else:
        reason = None
    
    return jsonify({"can_edit": can_edit, "reason": reason})


@users_bp.get("/<int:user_id>/profile")
@api_login_required
def get_user_profile(user_id: int):
    """Get a user's profile information with permission context."""
    from flask_login import current_user
    sess = g.db_session
    
    user = sess.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if current user can view this profile
    if not current_user.can_view_user(user_id):
        return jsonify({"error": "You do not have permission to view this profile"}), 403
    
    can_edit = current_user.can_edit_user(user_id)
    
    # Get household memberships
    households = []
    for membership in user.household_memberships:
        h = membership.household
        households.append({
            "id": h.id,
            "name": h.name,
            "role": membership.role,
            "joined_date": membership.joined_date.isoformat() if membership.joined_date else None
        })
    
    # Get family relationships
    relationships = []
    for rel in user.family_relationships:
        relationships.append({
            "id": rel.id,
            "related_user_id": rel.related_user_id,
            "related_user_name": rel.related_user.display_name,
            "relationship_type": rel.relationship_type,
            "notes": rel.notes
        })
    
    profile = {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "first_name": user.first_name,
        "middle_name": user.middle_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "address": user.address,
        "birthday": user.birthday.isoformat() if user.birthday else None,
        "death_date": user.death_date.isoformat() if user.death_date else None,
        "adoption_date": user.adoption_date.isoformat() if user.adoption_date else None,
        "sex": user.sex,
        "gender": user.gender,
        "notes": user.notes,
        "age": user.age,
        "is_record_only": user.is_record_only,
        "gravatar_url": user.gravatar_url(size=200),
        "households": households,
        "relationships": relationships,
        "can_edit": can_edit,
        "groups": [g.name for g in user.groups] if can_edit else []  # Only show groups if can edit
    }
    
    return jsonify(profile)


@users_bp.get("/groups")
@api_require_groups(["admin", "super-admin"])
def list_groups():
    sess = g.db_session
    groups = sess.scalars(select(Group)).all()
    return jsonify([{"id": g.id, "name": g.name, "description": g.description} for g in groups])
