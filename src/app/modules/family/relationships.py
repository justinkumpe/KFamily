"""Routes for direct user-to-user family relationships."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select, or_

from .models import UserRelationship
from ..users.models import User
from ...utils.auth import api_login_required, api_require_groups


relationships_bp = Blueprint("relationships", __name__)


def get_reciprocal_relationship(relationship_type: str, user_sex: str | None = None) -> str:
    """
    Get the reciprocal relationship type for automatic bidirectional links.
    
    Args:
        relationship_type: The original relationship type
        user_sex: The sex of the user who has this relationship (for gendered reciprocals)
    
    Returns:
        The reciprocal relationship type
    """
    # For son/daughter, return gendered parent type based on user's sex
    if relationship_type in ["son", "daughter", "child"]:
        if user_sex == "male":
            return "father"
        elif user_sex == "female":
            return "mother"
        else:
            return "parent"
    
    # For brother/sister, return gendered sibling based on user's sex
    if relationship_type in ["brother", "sister", "sibling"]:
        if user_sex == "male":
            return "brother"
        elif user_sex == "female":
            return "sister"
        else:
            return "sibling"
    
    # Standard reciprocals (non-gendered or fixed)
    reciprocals = {
        # Parent-child relationships (parent -> child direction)
        "parent": "child",  # Will be gendered based on child's sex
        "father": "child",  # Will be gendered as son/daughter based on child's sex
        "mother": "child",  # Will be gendered as son/daughter based on child's sex
        
        # Adoptive parent-child relationships
        "adoptive-parent": "child",
        "adoptive-father": "child",
        "adoptive-mother": "child",
        
        # Spouse relationships (bidirectional)
        "spouse": "spouse",
        
        # Grandparent-grandchild relationships
        "grandparent": "grandchild",
        "grandchild": "grandparent",
        
        # Default
        "other": "other",
    }
    
    base_reciprocal = reciprocals.get(relationship_type, "other")
    
    # Gender the "child" reciprocal based on child's sex
    if base_reciprocal == "child" and user_sex:
        if user_sex == "male":
            return "son"
        elif user_sex == "female":
            return "daughter"
        else:
            return "child"
    
    return base_reciprocal


@relationships_bp.get("/user/<int:user_id>")
@api_login_required
def get_user_relationships(user_id: int):
    """Get all direct family relationships for a user."""
    sess = current_app.session
    
    # Get relationships where user is the primary
    outgoing = sess.scalars(
        select(UserRelationship).where(UserRelationship.user_id == user_id)
    ).all()
    
    # Get relationships where user is the related_user
    incoming = sess.scalars(
        select(UserRelationship).where(UserRelationship.related_user_id == user_id)
    ).all()
    
    result = {
        "outgoing": [
            {
                "id": r.id,
                "related_user_id": r.related_user_id,
                "related_user_name": r.related_user.display_name,
                "relationship_type": r.relationship_type,
                "notes": r.notes,
                "created_date": r.created_date.isoformat() if r.created_date else None,
            }
            for r in outgoing
        ],
        "incoming": [
            {
                "id": r.id,
                "from_user_id": r.user_id,
                "from_user_name": r.user.display_name,
                "relationship_type": r.relationship_type,
                "notes": r.notes,
                "created_date": r.created_date.isoformat() if r.created_date else None,
            }
            for r in incoming
        ]
    }
    
    return jsonify(result)


@relationships_bp.post("")
@api_login_required
def create_relationship():
    """
    Create a direct family relationship between two users.
    Anyone can create relationships, but typically:
    - A parent adds their child
    - A sibling adds their sibling
    etc.
    """
    data = request.get_json(force=True)
    sess = current_app.session
    
    user_id = data.get("user_id")
    related_user_id = data.get("related_user_id")
    relationship_type = data.get("relationship_type")
    
    # Debug logging
    current_app.logger.info(f"CREATE RELATIONSHIP - Received: user_id={user_id}, related_user_id={related_user_id}, type={relationship_type}")
    
    if not all([user_id, related_user_id, relationship_type]):
        return jsonify({"error": "user_id, related_user_id, and relationship_type are required"}), 400
    
    # Validate users exist
    user = sess.get(User, user_id)
    related_user = sess.get(User, related_user_id)
    
    if not user or not related_user:
        return jsonify({"error": "One or both users not found"}), 404
    
    # Check for existing relationship
    existing = sess.scalar(
        select(UserRelationship).where(
            UserRelationship.user_id == user_id,
            UserRelationship.related_user_id == related_user_id,
            UserRelationship.relationship_type == relationship_type
        )
    )
    
    if existing:
        return jsonify({"error": "Relationship already exists"}), 400
    
    # Create primary relationship
    relationship = UserRelationship(
        user_id=user_id,
        related_user_id=related_user_id,
        relationship_type=relationship_type,
        notes=data.get("notes"),
        created_date=data.get("created_date"),
    )
    sess.add(relationship)
    
    # Create reciprocal relationship automatically
    # Determine which user's sex to use for gendered reciprocals:
    # 
    # Example: "Test is son of Justin"
    #   - user = Test, related_user = Justin, relationship_type = "son"
    #   - Test is the child, Justin is the parent
    #   - Reciprocal: "Justin is ??? of Test"
    #   - To determine if Justin is "father" or "mother", use Justin's (related_user's) sex
    #
    # For child->parent direction (son/daughter/child):
    #   - Use the PARENT's (related_user's) sex to determine father/mother/parent
    #
    # For parent->child direction (father/mother/parent):
    #   - Use the CHILD's (related_user's) sex to determine son/daughter/child
    #
    # For sibling direction (brother/sister/sibling):
    #   - Use the OTHER person's (user's) sex to determine brother/sister/sibling
    
    if relationship_type in ["son", "daughter", "child"]:
        # User is the child, related_user is the parent
        # Use parent's sex to determine father/mother/parent
        reciprocal_type = get_reciprocal_relationship(relationship_type, related_user.sex)
    elif relationship_type in ["father", "mother", "parent"]:
        # User is the parent, related_user is the child
        # Use child's sex to determine son/daughter/child
        reciprocal_type = get_reciprocal_relationship(relationship_type, related_user.sex)
    elif relationship_type in ["brother", "sister", "sibling"]:
        # Siblings - use the user's sex for the reciprocal
        reciprocal_type = get_reciprocal_relationship(relationship_type, user.sex)
    else:
        reciprocal_type = get_reciprocal_relationship(relationship_type)
    
    # Check if reciprocal already exists
    existing_reciprocal = sess.scalar(
        select(UserRelationship).where(
            UserRelationship.user_id == related_user_id,
            UserRelationship.related_user_id == user_id,
            UserRelationship.relationship_type == reciprocal_type
        )
    )
    
    if not existing_reciprocal:
        reciprocal = UserRelationship(
            user_id=related_user_id,
            related_user_id=user_id,
            relationship_type=reciprocal_type,
            notes=f"Auto-created from {user.display_name}'s {relationship_type} relationship",
            created_date=data.get("created_date"),
        )
        sess.add(reciprocal)
    
    sess.commit()
    
    return jsonify({
        "id": relationship.id,
        "user_id": relationship.user_id,
        "related_user_id": relationship.related_user_id,
        "relationship_type": relationship.relationship_type,
        "reciprocal_created": not existing_reciprocal,
        "reciprocal_type": reciprocal_type,
    }), 201


@relationships_bp.delete("/<int:relationship_id>")
@api_login_required
def delete_relationship(relationship_id: int):
    """Delete a direct family relationship and its reciprocal."""
    sess = current_app.session
    relationship = sess.get(UserRelationship, relationship_id)
    
    if not relationship:
        return jsonify({"error": "Relationship not found"}), 404
    
    # Get user objects to determine gendered reciprocals
    user = relationship.user
    related_user = relationship.related_user
    
    # Determine reciprocal type using same logic as creation
    if relationship.relationship_type in ["son", "daughter", "child"]:
        reciprocal_type = get_reciprocal_relationship(relationship.relationship_type, user.sex)
    elif relationship.relationship_type in ["father", "mother", "parent"]:
        reciprocal_type = get_reciprocal_relationship(relationship.relationship_type, related_user.sex)
    elif relationship.relationship_type in ["brother", "sister", "sibling"]:
        reciprocal_type = get_reciprocal_relationship(relationship.relationship_type, user.sex)
    else:
        reciprocal_type = get_reciprocal_relationship(relationship.relationship_type)
    
    # Find and delete reciprocal relationship
    reciprocal = sess.scalar(
        select(UserRelationship).where(
            UserRelationship.user_id == relationship.related_user_id,
            UserRelationship.related_user_id == relationship.user_id,
            UserRelationship.relationship_type == reciprocal_type
        )
    )
    
    # Delete both
    sess.delete(relationship)
    if reciprocal:
        sess.delete(reciprocal)
    
    sess.commit()
    
    return jsonify({"success": True, "reciprocal_deleted": reciprocal is not None}), 200


@relationships_bp.post("/user/<int:user_id>/update-reciprocals")
@api_login_required
def update_user_reciprocals(user_id: int):
    """
    Update all reciprocal relationships when user's sex changes.
    This ensures that gendered relationships (father/mother, son/daughter) are correct.
    """
    sess = current_app.session
    user = sess.get(User, user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    updated_count = 0
    
    # Get all relationships where this user is involved
    # 1. Outgoing: where user is the primary
    outgoing = sess.scalars(
        select(UserRelationship).where(UserRelationship.user_id == user_id)
    ).all()
    
    # 2. Incoming: where user is the related_user
    incoming = sess.scalars(
        select(UserRelationship).where(UserRelationship.related_user_id == user_id)
    ).all()
    
    # Update reciprocals for outgoing relationships
    for rel in outgoing:
        related_user = sess.get(User, rel.related_user_id)
        if not related_user:
            continue
            
        # Determine correct reciprocal type
        if rel.relationship_type in ["son", "daughter", "child"]:
            correct_reciprocal = get_reciprocal_relationship(rel.relationship_type, related_user.sex)
        elif rel.relationship_type in ["father", "mother", "parent"]:
            correct_reciprocal = get_reciprocal_relationship(rel.relationship_type, related_user.sex)
        elif rel.relationship_type in ["brother", "sister", "sibling"]:
            correct_reciprocal = get_reciprocal_relationship(rel.relationship_type, user.sex)
        else:
            correct_reciprocal = get_reciprocal_relationship(rel.relationship_type)
        
        # Find the reciprocal relationship
        reciprocal = sess.scalar(
            select(UserRelationship).where(
                UserRelationship.user_id == rel.related_user_id,
                UserRelationship.related_user_id == user_id
            )
        )
        
        if reciprocal and reciprocal.relationship_type != correct_reciprocal:
            reciprocal.relationship_type = correct_reciprocal
            updated_count += 1
    
    # Update reciprocals for incoming relationships (where this user is the related_user)
    for rel in incoming:
        primary_user = sess.get(User, rel.user_id)
        if not primary_user:
            continue
        
        # This relationship is FROM primary_user TO this user
        # We need to find what the reciprocal SHOULD be based on updated sex
        if rel.relationship_type in ["son", "daughter", "child"]:
            # primary_user is child, this user is parent
            # Reciprocal should be based on this user's sex
            correct_reciprocal = get_reciprocal_relationship(rel.relationship_type, user.sex)
        elif rel.relationship_type in ["father", "mother", "parent"]:
            # primary_user is parent, this user is child
            # Reciprocal should be based on this user's sex
            correct_reciprocal = get_reciprocal_relationship(rel.relationship_type, user.sex)
        elif rel.relationship_type in ["brother", "sister", "sibling"]:
            # Siblings - reciprocal based on primary_user's sex
            correct_reciprocal = get_reciprocal_relationship(rel.relationship_type, primary_user.sex)
        else:
            correct_reciprocal = get_reciprocal_relationship(rel.relationship_type)
        
        # Find the reciprocal (from this user to primary_user)
        reciprocal = sess.scalar(
            select(UserRelationship).where(
                UserRelationship.user_id == user_id,
                UserRelationship.related_user_id == rel.user_id
            )
        )
        
        if reciprocal and reciprocal.relationship_type != correct_reciprocal:
            reciprocal.relationship_type = correct_reciprocal
            updated_count += 1
    
    sess.commit()
    
    return jsonify({
        "success": True,
        "updated_count": updated_count,
        "message": f"Updated {updated_count} reciprocal relationships"
    }), 200

