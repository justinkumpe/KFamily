"""Timeline event models for tracking user life events across modules."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.modules.users.models import User


class TimelineEvent(Base):
    """
    Timeline event model for storing user life events.
    
    Events can come from various modules (family, health, education, etc.)
    and have different visibility levels for privacy control.
    """

    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    # Event details
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50))  # birth, adoption, death, marriage, etc.
    module_name: Mapped[str] = mapped_column(String(50))  # family, health, education, etc.
    
    # Core event info
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Privacy control
    visibility: Mapped[str] = mapped_column(
        String(20),
        default="private"
    )  # public, family, household, parents, private
    
    # Module-specific data stored as JSON
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Auto-generated flag (for birth/death/adoption events that sync with user fields)
    is_auto_generated: Mapped[bool] = mapped_column(default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="timeline_events")

    def __repr__(self):
        return f"<TimelineEvent {self.id}: {self.title} ({self.event_date})>"

    def to_dict(self, include_metadata: bool = True) -> dict:
        """Convert timeline event to dictionary."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "event_type": self.event_type,
            "module_name": self.module_name,
            "title": self.title,
            "description": self.description,
            "visibility": self.visibility,
            "is_auto_generated": self.is_auto_generated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_metadata and self.event_metadata:
            data["metadata"] = self.event_metadata
            
        return data
