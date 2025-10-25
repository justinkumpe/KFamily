"""API routes for managing life events."""
from __future__ import annotations

from datetime import date
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select

from .models_genogram import LifeEvent, LifeEventType
from ..users.models import User
from ...utils.auth import api_login_required


life_events_bp = Blueprint("life_events", __name__)


@life_events_bp.post("")
@api_login_required
def create_life_event():
    """Create a new life event."""
    data = request.get_json()
    sess = current_app.session
    
    # Validate required fields
    if not all(k in data for k in ['user_id', 'event_type', 'title', 'event_date']):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Validate user exists
    user = sess.get(User, data['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Create life event
    life_event = LifeEvent(
        user_id=data['user_id'],
        event_type=LifeEventType(data['event_type']),
        title=data['title'],
        description=data.get('description'),
        event_date=date.fromisoformat(data['event_date']),
        end_date=date.fromisoformat(data['end_date']) if data.get('end_date') else None,
        location=data.get('location'),
        related_user_id=data.get('related_user_id'),
        related_partnership_id=data.get('related_partnership_id'),
        is_private=data.get('is_private', False),
        show_on_genogram=data.get('show_on_genogram', True),
    )
    
    sess.add(life_event)
    sess.commit()
    
    return jsonify(_life_event_to_dict(life_event)), 201


@life_events_bp.get("/<int:event_id>")
@api_login_required
def get_life_event(event_id: int):
    """Get a specific life event."""
    sess = current_app.session
    life_event = sess.get(LifeEvent, event_id)
    
    if not life_event:
        return jsonify({"error": "Life event not found"}), 404
    
    return jsonify(_life_event_to_dict(life_event))


@life_events_bp.put("/<int:event_id>")
@api_login_required
def update_life_event(event_id: int):
    """Update a life event."""
    data = request.get_json()
    sess = current_app.session
    
    life_event = sess.get(LifeEvent, event_id)
    if not life_event:
        return jsonify({"error": "Life event not found"}), 404
    
    # Update fields
    if 'event_type' in data:
        life_event.event_type = LifeEventType(data['event_type'])
    if 'title' in data:
        life_event.title = data['title']
    if 'description' in data:
        life_event.description = data['description']
    if 'event_date' in data:
        life_event.event_date = date.fromisoformat(data['event_date'])
    if 'end_date' in data:
        life_event.end_date = date.fromisoformat(data['end_date']) if data['end_date'] else None
    if 'location' in data:
        life_event.location = data['location']
    if 'related_user_id' in data:
        life_event.related_user_id = data['related_user_id']
    if 'related_partnership_id' in data:
        life_event.related_partnership_id = data['related_partnership_id']
    if 'is_private' in data:
        life_event.is_private = data['is_private']
    if 'show_on_genogram' in data:
        life_event.show_on_genogram = data['show_on_genogram']
    
    sess.commit()
    
    return jsonify(_life_event_to_dict(life_event))


@life_events_bp.delete("/<int:event_id>")
@api_login_required
def delete_life_event(event_id: int):
    """Delete a life event."""
    sess = current_app.session
    life_event = sess.get(LifeEvent, event_id)
    
    if not life_event:
        return jsonify({"error": "Life event not found"}), 404
    
    sess.delete(life_event)
    sess.commit()
    
    return jsonify({"message": "Life event deleted"}), 200


@life_events_bp.get("/user/<int:user_id>")
@api_login_required
def get_user_life_events(user_id: int):
    """Get all life events for a specific user."""
    sess = current_app.session
    
    # Verify user exists
    user = sess.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get life events
    life_events = sess.scalars(
        select(LifeEvent).where(
            LifeEvent.user_id == user_id
        ).order_by(LifeEvent.event_date.desc())
    ).all()
    
    return jsonify([_life_event_to_dict(e) for e in life_events])


def _life_event_to_dict(life_event: LifeEvent) -> dict:
    """Convert life event to dictionary."""
    result = {
        'id': life_event.id,
        'user_id': life_event.user_id,
        'event_type': life_event.event_type.value,
        'title': life_event.title,
        'description': life_event.description,
        'event_date': life_event.event_date.isoformat(),
        'end_date': life_event.end_date.isoformat() if life_event.end_date else None,
        'location': life_event.location,
        'related_user_id': life_event.related_user_id,
        'related_partnership_id': life_event.related_partnership_id,
        'is_private': life_event.is_private,
        'show_on_genogram': life_event.show_on_genogram,
        'created_at': life_event.created_at.isoformat(),
        'updated_at': life_event.updated_at.isoformat(),
    }
    
    # Include related user info if present
    if life_event.related_user:
        result['related_user'] = {
            'id': life_event.related_user.id,
            'display_name': life_event.related_user.display_name,
        }
    
    return result
