from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select

from .models import Household, Person, HouseholdMember
from ..users.models import User
from ...utils.auth import api_login_required, api_require_groups


family_bp = Blueprint("family", __name__)


@family_bp.get("/households")
@api_login_required
def list_households():
    """List households visible to the current user."""
    from flask_login import current_user
    sess = current_app.session
    
    # Get all households
    all_households = sess.scalars(select(Household)).all()
    
    # Filter to only households where user is a member (unless admin)
    if current_user.has_any_group("admin", "super-admin"):
        visible_households = all_households
    else:
        # Only show households where user is a member
        user_household_ids = {m.household_id for m in current_user.household_memberships}
        visible_households = [h for h in all_households if h.id in user_household_ids]
    
    return jsonify([
        {
            "id": h.id,
            "name": h.name,
            "address": h.address,
            "phone": h.phone,
            "email": h.email,
            "members": [
                {
                    "id": m.id,
                    "user_id": m.user_id,
                    "display_name": m.user.display_name,
                    "email": m.user.email,
                    "role": m.role,
                    "notes": m.notes,
                    "joined_date": m.joined_date.isoformat() if m.joined_date else None,
                }
                for m in h.members
            ],
        }
        for h in visible_households
    ])


@family_bp.post("/households")
@api_require_groups(["family-editor", "family-admin", "admin", "super-admin"])
def create_household():
    data = request.get_json(force=True)
    h = Household(
        name=data["name"],
        address=data.get("address"),
        phone=data.get("phone"),
        email=data.get("email"),
    )
    current_app.session.add(h)
    current_app.session.commit()
    return jsonify({"id": h.id, "name": h.name}), 201


@family_bp.post("/households/<int:household_id>/persons")
@api_require_groups(["family-editor", "family-admin", "admin", "super-admin"])
def add_person(household_id: int):
    data = request.get_json(force=True)
    p = Person(
        household_id=household_id,
        first_name=data["first_name"],
        last_name=data["last_name"],
        birthday=data.get("birthday"),
        sex=data.get("sex"),
        gender=data.get("gender"),
        phone=data.get("phone"),
        email=data.get("email"),
        relation=data.get("relation"),
    )
    current_app.session.add(p)
    current_app.session.commit()
    return jsonify({"id": p.id, "household_id": p.household_id}), 201


@family_bp.post("/households/<int:household_id>/members")
@api_require_groups(["family-editor", "family-admin", "admin", "super-admin"])
def add_household_member(household_id: int):
    """Add a user to a household with a specific relationship type."""
    data = request.get_json(force=True)
    sess = current_app.session
    
    # Validate household exists
    household = sess.get(Household, household_id)
    if not household:
        return jsonify({"error": "Household not found"}), 404
    
    # Validate user exists
    user_id = data.get("user_id")
    user = sess.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if user is already a member of this household
    existing = sess.scalar(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == user_id
        )
    )
    if existing:
        return jsonify({"error": "User is already a member of this household"}), 400
    
    # Create household member
    member = HouseholdMember(
        household_id=household_id,
        user_id=user_id,
        role=data.get("role", "user"),  # admin, user, or view-only
        notes=data.get("notes"),
        joined_date=data.get("joined_date"),
    )
    sess.add(member)
    sess.commit()
    
    return jsonify({
        "id": member.id,
        "household_id": member.household_id,
        "user_id": member.user_id,
        "display_name": member.user.display_name,
        "role": member.role,
    }), 201


@family_bp.delete("/households/<int:household_id>/members/<int:member_id>")
@api_require_groups(["family-editor", "family-admin", "admin", "super-admin"])
def remove_household_member(household_id: int, member_id: int):
    """Remove a user from a household."""
    sess = current_app.session
    
    # Validate household member exists and belongs to this household
    member = sess.get(HouseholdMember, member_id)
    if not member:
        return jsonify({"error": "Household member not found"}), 404
    
    if member.household_id != household_id:
        return jsonify({"error": "Member does not belong to this household"}), 400
    
    sess.delete(member)
    sess.commit()
    
    return jsonify({"success": True}), 200


@family_bp.delete("/households/<int:household_id>")
@api_require_groups(["family-admin", "admin", "super-admin"])
def delete_household(household_id: int):
    """Delete a household. Only admins can delete households."""
    sess = current_app.session
    
    household = sess.get(Household, household_id)
    if not household:
        return jsonify({"error": "Household not found"}), 404
    
    # Delete the household (members will be cascade deleted)
    sess.delete(household)
    sess.commit()
    
    return jsonify({"success": True}), 200
