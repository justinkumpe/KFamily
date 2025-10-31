"""Timeline API routes for managing user timeline events."""

from datetime import datetime

from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy import select

from app.utils.auth import api_login_required
from app.modules.users.models import User
from app.modules.family.models import UserRelationship
from .models import TimelineEvent
from .templates import get_all_templates, get_template, list_templates_for_module

timeline_bp = Blueprint("timeline", __name__, url_prefix="/api/timeline")


@timeline_bp.get("/templates")
@api_login_required
def list_event_templates():
    """
    List all available timeline event templates.
    
    Query params:
        - module: Filter by module name
    """
    module_filter = request.args.get("module")
    
    if module_filter:
        templates = list_templates_for_module(module_filter)
        return jsonify([t.to_dict() for t in templates])
    else:
        templates = get_all_templates()
        return jsonify({
            event_type: template.to_dict()
            for event_type, template in templates.items()
        })


@timeline_bp.get("/templates/<event_type>")
@api_login_required
def get_event_template(event_type: str):
    """Get details for a specific event template."""
    template = get_template(event_type)
    
    if not template:
        return jsonify({"error": "Template not found"}), 404
    
    return jsonify(template.to_dict())


def can_view_timeline_event(current_user: User, event: TimelineEvent) -> bool:
    """
    Check if current user can view a timeline event based on visibility settings.
    
    Args:
        current_user: The currently logged-in user
        event: The timeline event to check
        
    Returns:
        True if user can view the event, False otherwise
    """
    # User can always view their own events
    if current_user.id == event.user_id:
        return True
    
    # Admins and super-admins can view all events
    if any(g.name in ["admin", "super-admin"] for g in current_user.groups):
        return True
    
    # Check visibility level
    if event.visibility == "public":
        return True
    
    if event.visibility == "private":
        return False
    
    sess = g.db_session
    event_user = sess.get(User, event.user_id)
    
    if event.visibility == "family":
        # Check if users are family members (have any relationship)
        return current_user.is_family_member(event.user_id)
    
    if event.visibility == "household":
        # Check if users share a household
        return current_user.shares_household(event.user_id)
    
    if event.visibility == "parents":
        # Check if current user is a parent of the event owner
        parent_rels = sess.scalars(
            select(event_user.family_relationships).where(
                event_user.family_relationships.c.relationship_type.in_(["father", "mother", "parent"])
            )
        ).all()
        return current_user.id in [rel.related_user_id for rel in parent_rels]
    
    return False


def _get_family_timeline_events(user: User, session, module_filter=None, event_type_filter=None):
    """
    Get timeline events for family members that should appear on user's timeline.
    
    Includes:
    - Birth/adoption/death dates of children, grandchildren, siblings, aunts, and uncles
    - Death dates of parents and grandparents (that occurred after user's birth/adoption)
    
    Args:
        user: The user whose timeline we're building
        session: Database session
        module_filter: Optional module filter
        event_type_filter: Optional event type filter
        
    Returns:
        List of TimelineEvent objects
    """
    family_events = []
    user_birth_date = user.birthday or user.adoption_date
    
    # Get all relationships for this user
    relationships = session.scalars(
        select(UserRelationship).where(UserRelationship.user_id == user.id)
    ).all()
    
    # Define which relationships to include
    # Children: son, daughter, child
    # Grandchildren: grandson, granddaughter, grandchild
    # Siblings: brother, sister, sibling
    # Aunts/Uncles: aunt, uncle
    # Parents: father, mother, parent, adoptive-father, adoptive-mother
    # Grandparents: grandfather, grandmother, grandparent
    descendant_types = {"son", "daughter", "child", "grandson", "granddaughter", "grandchild"}
    sibling_types = {"brother", "sister", "sibling"}
    aunt_uncle_types = {"aunt", "uncle"}
    ancestor_types = {"father", "mother", "parent", "adoptive-father", "adoptive-mother", 
                     "grandfather", "grandmother", "grandparent"}
    
    for rel in relationships:
        related_user_id = rel.related_user_id
        rel_type = rel.relationship_type
        
        # Build query for related user's events
        query = select(TimelineEvent).where(
            TimelineEvent.user_id == related_user_id,
            TimelineEvent.is_auto_generated.is_(True)  # Only auto-generated life events
        )
        
        # For descendants (children/grandchildren): include birth, adoption, and death
        if rel_type in descendant_types:
            query = query.where(
                TimelineEvent.event_type.in_(["birth", "adoption", "death"])
            )
        
        # For siblings: include birth, adoption, and death
        elif rel_type in sibling_types:
            query = query.where(
                TimelineEvent.event_type.in_(["birth", "adoption", "death"])
            )
        
        # For aunts/uncles: include birth, adoption, and death
        elif rel_type in aunt_uncle_types:
            query = query.where(
                TimelineEvent.event_type.in_(["birth", "adoption", "death"])
            )
        
        # For ancestors (parents/grandparents): only include death dates after user's birth
        elif rel_type in ancestor_types:
            query = query.where(TimelineEvent.event_type == "death")
            if user_birth_date:
                query = query.where(TimelineEvent.event_date >= user_birth_date)
        else:
            # Skip other relationship types
            continue
        
        # Apply filters if provided
        if module_filter:
            query = query.where(TimelineEvent.module_name == module_filter)
        
        if event_type_filter:
            query = query.where(TimelineEvent.event_type == event_type_filter)
        
        # Add matching events
        events = session.scalars(query).all()
        family_events.extend(events)
    
    return family_events


@timeline_bp.get("/users/<int:user_id>")
@api_login_required
def get_user_timeline(user_id: int):
    """
    Get timeline events for a specific user.
    Includes:
    - User's own events
    - Birth/adoption/death dates of children, grandchildren, siblings, aunts, and uncles
    - Death dates of parents and grandparents (that occurred after user's birth/adoption)
    
    Query params:
        - module: Filter by module name
        - event_type: Filter by event type
        - limit: Maximum number of events to return
        - include_family: Include family events (default: true)
    """
    from flask_login import current_user
    sess = g.db_session
    
    # Check if user exists
    user = sess.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if current user can view this user's profile
    if not current_user.can_view_user(user_id):
        return jsonify({"error": "You do not have permission to view this user's timeline"}), 403
    
    # Build base query for user's own events
    query = select(TimelineEvent).where(TimelineEvent.user_id == user_id)
    
    # Apply filters
    module_filter = request.args.get("module")
    if module_filter:
        query = query.where(TimelineEvent.module_name == module_filter)
    
    event_type_filter = request.args.get("event_type")
    if event_type_filter:
        query = query.where(TimelineEvent.event_type == event_type_filter)
    
    events = list(sess.scalars(query).all())
    
    # Add family events if not disabled
    include_family = request.args.get("include_family", "true").lower() != "false"
    if include_family:
        family_events = _get_family_timeline_events(user, sess, module_filter, event_type_filter)
        events.extend(family_events)
    
    # Sort all events by date descending (newest first)
    events.sort(key=lambda e: e.event_date, reverse=True)
    
    # Apply limit after combining all events
    limit = request.args.get("limit", type=int)
    if limit:
        events = events[:limit]
    
    # Filter by visibility permissions
    visible_events = [
        event for event in events
        if can_view_timeline_event(current_user, event)
    ]
    
    return jsonify([event.to_dict() for event in visible_events])


@timeline_bp.post("/users/<int:user_id>")
@api_login_required
def create_timeline_event(user_id: int):
    """Create a new timeline event for a user."""
    from flask_login import current_user
    sess = g.db_session
    
    # Check if user exists
    user = sess.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if current user can edit this user
    if not current_user.can_edit_user(user_id):
        return jsonify({"error": "You do not have permission to add events for this user"}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ["event_date", "event_type", "module_name", "title"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Parse event date
    try:
        event_date = datetime.fromisoformat(data["event_date"]).date()
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid event_date format. Use ISO format (YYYY-MM-DD)"}), 400
    
    # Validate visibility
    valid_visibilities = ["public", "family", "household", "parents", "private"]
    visibility = data.get("visibility", "private")
    if visibility not in valid_visibilities:
        return jsonify({"error": f"Invalid visibility. Must be one of: {', '.join(valid_visibilities)}"}), 400
    
    # Create timeline event
    event = TimelineEvent(
        user_id=user_id,
        event_date=event_date,
        event_type=data["event_type"],
        module_name=data["module_name"],
        title=data["title"],
        description=data.get("description"),
        visibility=visibility,
        event_metadata=data.get("metadata"),
        is_auto_generated=False,
    )
    
    sess.add(event)
    sess.commit()
    
    return jsonify(event.to_dict()), 201


@timeline_bp.patch("/<int:event_id>")
@api_login_required
def update_timeline_event(event_id: int):
    """Update a timeline event."""
    from flask_login import current_user
    sess = g.db_session
    
    event = sess.get(TimelineEvent, event_id)
    if not event:
        return jsonify({"error": "Timeline event not found"}), 404
    
    # Check if current user can edit this user
    if not current_user.can_edit_user(event.user_id):
        return jsonify({"error": "You do not have permission to edit this event"}), 403
    
    # Don't allow editing auto-generated events through API
    if event.is_auto_generated:
        return jsonify({"error": "Cannot edit auto-generated events. Update user's life dates instead."}), 400
    
    data = request.get_json()
    
    # Update fields
    if "event_date" in data:
        try:
            event.event_date = datetime.fromisoformat(data["event_date"]).date()
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid event_date format. Use ISO format (YYYY-MM-DD)"}), 400
    
    if "event_type" in data:
        event.event_type = data["event_type"]
    
    if "title" in data:
        event.title = data["title"]
    
    if "description" in data:
        event.description = data["description"]
    
    if "visibility" in data:
        valid_visibilities = ["public", "family", "household", "parents", "private"]
        if data["visibility"] not in valid_visibilities:
            return jsonify({"error": f"Invalid visibility. Must be one of: {', '.join(valid_visibilities)}"}), 400
        event.visibility = data["visibility"]
    
    if "metadata" in data:
        event.event_metadata = data["metadata"]
    
    event.updated_at = datetime.utcnow()
    sess.commit()
    
    return jsonify(event.to_dict())


@timeline_bp.delete("/<int:event_id>")
@api_login_required
def delete_timeline_event(event_id: int):
    """Delete a timeline event."""
    from flask_login import current_user
    sess = g.db_session
    
    event = sess.get(TimelineEvent, event_id)
    if not event:
        return jsonify({"error": "Timeline event not found"}), 404
    
    # Check if current user can edit this user
    if not current_user.can_edit_user(event.user_id):
        return jsonify({"error": "You do not have permission to delete this event"}), 403
    
    # Don't allow deleting auto-generated events through API
    if event.is_auto_generated:
        return jsonify({"error": "Cannot delete auto-generated events"}), 400
    
    sess.delete(event)
    sess.commit()
    
    return jsonify({"message": "Timeline event deleted successfully"}), 200
