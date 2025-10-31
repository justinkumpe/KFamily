"""API routes for managing partnerships (marriages, relationships, etc.)."""
from __future__ import annotations

from datetime import date
from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy import select, or_

from .models_genogram import Partnership, RelationshipType, RelationshipQuality, CustodyType
from ..users.models import User
from ...utils.auth import api_login_required


partnerships_bp = Blueprint("partnerships", __name__)


@partnerships_bp.post("")
@api_login_required
def create_partnership():
    """Create a new partnership between two people."""
    data = request.get_json()
    sess = g.db_session
    
    # Validate required fields
    if not all(k in data for k in ['person1_id', 'person2_id', 'relationship_type']):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Validate users exist
    person1 = sess.get(User, data['person1_id'])
    person2 = sess.get(User, data['person2_id'])
    
    if not person1 or not person2:
        return jsonify({"error": "One or both users not found"}), 404
    
    # Can't partner with yourself
    if data['person1_id'] == data['person2_id']:
        return jsonify({"error": "Cannot create partnership with same person"}), 400
    
    # Create partnership
    partnership = Partnership(
        person1_id=data['person1_id'],
        person2_id=data['person2_id'],
        relationship_type=RelationshipType(data['relationship_type']),
        relationship_quality=RelationshipQuality(data['relationship_quality']) if data.get('relationship_quality') else None,
        start_date=date.fromisoformat(data['start_date']) if data.get('start_date') else None,
        end_date=date.fromisoformat(data['end_date']) if data.get('end_date') else None,
        location=data.get('location'),
        notes=data.get('notes'),
        has_children=data.get('has_children', False),
        custody_type=CustodyType(data['custody_type']) if data.get('custody_type') else None,
        custody_notes=data.get('custody_notes'),
    )
    
    sess.add(partnership)
    sess.commit()
    
    return jsonify(_partnership_to_dict(partnership)), 201


@partnerships_bp.get("/<int:partnership_id>")
@api_login_required
def get_partnership(partnership_id: int):
    """Get a specific partnership."""
    sess = g.db_session
    partnership = sess.get(Partnership, partnership_id)
    
    if not partnership:
        return jsonify({"error": "Partnership not found"}), 404
    
    return jsonify(_partnership_to_dict(partnership))


@partnerships_bp.put("/<int:partnership_id>")
@api_login_required
def update_partnership(partnership_id: int):
    """Update a partnership."""
    data = request.get_json()
    sess = g.db_session
    
    partnership = sess.get(Partnership, partnership_id)
    if not partnership:
        return jsonify({"error": "Partnership not found"}), 404
    
    # Update fields
    if 'relationship_type' in data:
        partnership.relationship_type = RelationshipType(data['relationship_type'])
    if 'relationship_quality' in data:
        partnership.relationship_quality = RelationshipQuality(data['relationship_quality']) if data['relationship_quality'] else None
    if 'start_date' in data:
        partnership.start_date = date.fromisoformat(data['start_date']) if data['start_date'] else None
    if 'end_date' in data:
        partnership.end_date = date.fromisoformat(data['end_date']) if data['end_date'] else None
    if 'location' in data:
        partnership.location = data['location']
    if 'notes' in data:
        partnership.notes = data['notes']
    if 'has_children' in data:
        partnership.has_children = data['has_children']
    if 'custody_type' in data:
        partnership.custody_type = CustodyType(data['custody_type']) if data['custody_type'] else None
    if 'custody_notes' in data:
        partnership.custody_notes = data['custody_notes']
    
    sess.commit()
    
    return jsonify(_partnership_to_dict(partnership))


@partnerships_bp.delete("/<int:partnership_id>")
@api_login_required
def delete_partnership(partnership_id: int):
    """Delete a partnership."""
    sess = g.db_session
    partnership = sess.get(Partnership, partnership_id)
    
    if not partnership:
        return jsonify({"error": "Partnership not found"}), 404
    
    sess.delete(partnership)
    sess.commit()
    
    return jsonify({"message": "Partnership deleted"}), 200


@partnerships_bp.get("/user/<int:user_id>")
@api_login_required
def get_user_partnerships(user_id: int):
    """Get all partnerships for a specific user."""
    sess = g.db_session
    
    # Verify user exists
    user = sess.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get partnerships where user is either person1 or person2
    partnerships = sess.scalars(
        select(Partnership).where(
            or_(Partnership.person1_id == user_id, Partnership.person2_id == user_id)
        ).order_by(Partnership.start_date.desc())
    ).all()
    
    return jsonify([_partnership_to_dict(p) for p in partnerships])


def _partnership_to_dict(partnership: Partnership) -> dict:
    """Convert partnership to dictionary."""
    return {
        'id': partnership.id,
        'person1_id': partnership.person1_id,
        'person2_id': partnership.person2_id,
        'person1': {
            'id': partnership.person1.id,
            'display_name': partnership.person1.display_name,
            'first_name': partnership.person1.first_name,
            'last_name': partnership.person1.last_name,
        },
        'person2': {
            'id': partnership.person2.id,
            'display_name': partnership.person2.display_name,
            'first_name': partnership.person2.first_name,
            'last_name': partnership.person2.last_name,
        },
        'relationship_type': partnership.relationship_type.value,
        'relationship_quality': partnership.relationship_quality.value if partnership.relationship_quality else None,
        'start_date': partnership.start_date.isoformat() if partnership.start_date else None,
        'end_date': partnership.end_date.isoformat() if partnership.end_date else None,
        'location': partnership.location,
        'notes': partnership.notes,
        'has_children': partnership.has_children,
        'custody_type': partnership.custody_type.value if partnership.custody_type else None,
        'custody_notes': partnership.custody_notes,
        'created_at': partnership.created_at.isoformat(),
        'updated_at': partnership.updated_at.isoformat(),
    }
