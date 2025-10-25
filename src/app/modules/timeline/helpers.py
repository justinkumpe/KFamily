"""Helper functions for managing timeline events."""

from datetime import date
from typing import Optional

from sqlalchemy import select

from app.modules.users.models import User
from .models import TimelineEvent


def sync_user_life_events(user: User, session) -> None:
    """
    Synchronize user's life events (birth, adoption, death) with timeline.
    Creates or updates auto-generated timeline events based on user's dates.
    
    Args:
        user: User object to sync events for
        session: Database session
    """
    # Sync birth event
    if user.birthday:
        _sync_event(
            user=user,
            session=session,
            event_type="birth",
            event_date=user.birthday,
            title=f"{user.first_name or user.display_name} was born",
            description=None,
            visibility="family"
        )
    else:
        _delete_auto_event(user.id, "birth", session)
    
    # Sync adoption event
    if user.adoption_date:
        _sync_event(
            user=user,
            session=session,
            event_type="adoption",
            event_date=user.adoption_date,
            title=f"{user.first_name or user.display_name} was adopted",
            description=None,
            visibility="family"
        )
    else:
        _delete_auto_event(user.id, "adoption", session)
    
    # Sync death event
    if user.death_date:
        age_str = ""
        if user.age is not None:
            age_str = f" at age {user.age}"
        _sync_event(
            user=user,
            session=session,
            event_type="death",
            event_date=user.death_date,
            title=f"{user.first_name or user.display_name} passed away{age_str}",
            description=None,
            visibility="family"
        )
    else:
        _delete_auto_event(user.id, "death", session)


def _sync_event(
    user: User,
    session,
    event_type: str,
    event_date: date,
    title: str,
    description: Optional[str],
    visibility: str
) -> TimelineEvent:
    """
    Create or update an auto-generated timeline event.
    
    Args:
        user: User object
        session: Database session
        event_type: Type of event (birth, adoption, death)
        event_date: Date of the event
        title: Event title
        description: Event description (optional)
        visibility: Visibility level
        
    Returns:
        The created or updated TimelineEvent
    """
    # Check if event already exists
    existing = session.scalar(
        select(TimelineEvent).where(
            TimelineEvent.user_id == user.id,
            TimelineEvent.event_type == event_type,
            TimelineEvent.is_auto_generated == True
        )
    )
    
    if existing:
        # Update existing event
        existing.event_date = event_date
        existing.title = title
        existing.description = description
        existing.visibility = visibility
        return existing
    else:
        # Create new event
        event = TimelineEvent(
            user_id=user.id,
            event_date=event_date,
            event_type=event_type,
            module_name="family",
            title=title,
            description=description,
            visibility=visibility,
            is_auto_generated=True
        )
        session.add(event)
        return event


def _delete_auto_event(user_id: int, event_type: str, session) -> None:
    """
    Delete an auto-generated timeline event if it exists.
    
    Args:
        user_id: ID of the user
        event_type: Type of event to delete
        session: Database session
    """
    event = session.scalar(
        select(TimelineEvent).where(
            TimelineEvent.user_id == user_id,
            TimelineEvent.event_type == event_type,
            TimelineEvent.is_auto_generated == True
        )
    )
    
    if event:
        session.delete(event)


def create_event_for_user(
    user_id: int,
    event_date: date,
    event_type: str,
    module_name: str,
    title: str,
    description: Optional[str] = None,
    visibility: str = "private",
    metadata: Optional[dict] = None,
    session=None
) -> TimelineEvent:
    """
    Create a new timeline event for a user.
    
    Args:
        user_id: ID of the user
        event_date: Date of the event
        event_type: Type of event
        module_name: Name of the module creating the event
        title: Event title
        description: Event description (optional)
        visibility: Visibility level (default: private)
        metadata: Module-specific metadata (optional)
        session: Database session
        
    Returns:
        The created TimelineEvent
    """
    event = TimelineEvent(
        user_id=user_id,
        event_date=event_date,
        event_type=event_type,
        module_name=module_name,
        title=title,
        description=description,
        visibility=visibility,
        event_metadata=metadata,
        is_auto_generated=False
    )
    
    session.add(event)
    return event
