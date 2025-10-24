from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, render_template
from sqlalchemy import select

from .models import User, Group, INITIAL_GROUPS
from ..family.models import UserRelationship
from ..family.relationships import get_reciprocal_relationship
from ...utils.auth import api_require_groups, api_allow_household_parent, api_login_required


users_bp = Blueprint("users", __name__)


@users_bp.post("/seed-groups")
def seed_groups():
    sess = current_app.session
    existing = {g.name for g in sess.scalars(select(Group)).all()}
    created = []
    for name in INITIAL_GROUPS:
        if name not in existing:
            g = Group(name=name, description=name)
            sess.add(g)
            created.append(name)
    sess.commit()
    return jsonify({"created": created, "skipped": list(existing & set(INITIAL_GROUPS))})


@users_bp.get("/admin-page")
@api_require_groups(["admin", "super-admin"])
def admin_users_page_api():
    # Serve template through a non-API route in app.py
    return render_template("admin/users.html")


@users_bp.get("")
@api_require_groups(["admin", "super-admin"])
def list_users():
    sess = current_app.session
    users = sess.scalars(select(User)).all()
    return jsonify([
        {
            "id": u.id,
            "email": u.email,
            "display_name": u.display_name,
            "groups": [g.name for g in u.groups],
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
        for u in users
    ])


@users_bp.post("")
@api_require_groups(["admin", "super-admin"])
def create_user():
    data = request.get_json(force=True)
    user = User(
        email=data["email"],
        display_name=data.get("display_name", data["email"].split("@")[0]),
        password_hash=data.get("password_hash", "changeme"),
        first_name=data.get("first_name"),
        middle_name=data.get("middle_name"),
        last_name=data.get("last_name"),
        phone=data.get("phone"),
        address=data.get("address"),
        birthday=data.get("birthday"),
        death_date=data.get("death_date"),
        adoption_date=data.get("adoption_date"),
        sex=data.get("sex"),
        gender=data.get("gender"),
        notes=data.get("notes"),
    )
    if "password" in data:
        user.set_password(data["password"])
    current_app.session.add(user)
    current_app.session.commit()
    return jsonify({"id": user.id, "email": user.email, "display_name": user.display_name}), 201


@users_bp.post("/<int:user_id>/groups")
@api_require_groups(["admin", "super-admin"])
def add_user_group(user_id: int):
    data = request.get_json(force=True)
    name = data.get("name")
    if not name:
        return jsonify({"error": "group name required"}), 400
    sess = current_app.session
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
    sess = current_app.session
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
    sess = current_app.session
    user = sess.get(User, user_id)
    if not user:
        return jsonify({"error": "not found"}), 404
    
    # Track if sex changed (to update reciprocal relationships)
    old_sex = user.sex
    sex_changed = False
    
    if "email" in data:
        user.email = data["email"]
    if "display_name" in data:
        user.display_name = data["display_name"]
    if "password" in data and data["password"]:
        user.set_password(data["password"])
    
    # Update family tree fields
    if "first_name" in data:
        user.first_name = data["first_name"] or None
    if "middle_name" in data:
        user.middle_name = data["middle_name"] or None
    if "last_name" in data:
        user.last_name = data["last_name"] or None
    if "phone" in data:
        user.phone = data["phone"] or None
    if "address" in data:
        user.address = data["address"] or None
    if "birthday" in data:
        user.birthday = data["birthday"] or None
    if "death_date" in data:
        user.death_date = data["death_date"] or None
    if "adoption_date" in data:
        user.adoption_date = data["adoption_date"] or None
    if "sex" in data:
        new_sex = data["sex"] or None
        if new_sex != old_sex:
            sex_changed = True
        user.sex = new_sex
    if "gender" in data:
        user.gender = data["gender"] or None
    if "notes" in data:
        user.notes = data["notes"] or None
    
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
    sess = current_app.session
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
    from flask_login import current_user
    
    # Admins can edit anyone
    if current_user.has_any_group("admin", "super-admin"):
        return jsonify({"can_edit": True, "reason": "admin"})
    
    # Check if current user is a household parent of the target user
    if current_user.can_edit_household_member(user_id):
        return jsonify({"can_edit": True, "reason": "household_parent"})
    
    # Check if editing self
    if current_user.id == user_id:
        return jsonify({"can_edit": True, "reason": "self"})
    
    return jsonify({"can_edit": False})


@users_bp.get("/groups")
@api_require_groups(["admin", "super-admin"])
def list_groups():
    sess = current_app.session
    groups = sess.scalars(select(Group)).all()
    return jsonify([{"id": g.id, "name": g.name, "description": g.description} for g in groups])
