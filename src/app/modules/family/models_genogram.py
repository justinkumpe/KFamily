"""Additional models for complete genogram functionality."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, Date, DateTime, Boolean, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from ...database import Base


class RelationshipType(str, enum.Enum):
    """Type of relationship between two people."""
    MARRIED = "married"
    DIVORCED = "divorced"
    SEPARATED = "separated"
    COMMON_LAW = "common_law"
    ENGAGED = "engaged"
    DATING = "dating"
    FORMER_PARTNER = "former_partner"
    WIDOWED = "widowed"


class RelationshipQuality(str, enum.Enum):
    """Quality/emotional tone of relationship."""
    CLOSE = "close"
    VERY_CLOSE = "very_close"
    DISTANT = "distant"
    ESTRANGED = "estranged"
    CONFLICTED = "conflicted"
    ABUSIVE = "abusive"
    NORMAL = "normal"


class CustodyType(str, enum.Enum):
    """Custody arrangement for children."""
    SOLE_MOTHER = "sole_mother"
    SOLE_FATHER = "sole_father"
    JOINT = "joint"
    SPLIT = "split"
    PRIMARY_MOTHER = "primary_mother"
    PRIMARY_FATHER = "primary_father"
    OTHER_GUARDIAN = "other_guardian"


class Partnership(Base):
    """
    Represents a romantic/marital partnership between two people.
    This is separate from UserRelationship which represents family connections.
    """
    __tablename__ = "partnerships"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # The two partners
    person1_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    person2_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Relationship details
    relationship_type: Mapped[RelationshipType] = mapped_column(
        SQLEnum(RelationshipType), nullable=False, default=RelationshipType.MARRIED
    )
    relationship_quality: Mapped[Optional[RelationshipQuality]] = mapped_column(
        SQLEnum(RelationshipQuality), nullable=True
    )
    
    # Important dates
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # Marriage/partnership date
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # Divorce/separation date
    
    # Additional info
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Where married
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Custody information (if applicable)
    has_children: Mapped[bool] = mapped_column(Boolean, default=False)
    custody_type: Mapped[Optional[CustodyType]] = mapped_column(
        SQLEnum(CustodyType), nullable=True
    )
    custody_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships to users
    person1: Mapped["User"] = relationship("User", foreign_keys=[person1_id], back_populates="partnerships_as_person1")
    person2: Mapped["User"] = relationship("User", foreign_keys=[person2_id], back_populates="partnerships_as_person2")


class Household(Base):
    """
    Represents a household/family unit - people living together.
    """
    __tablename__ = "households"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "The Kumpe Household"
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Dates
    established_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    dissolved_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to members
    members: Mapped[list["HouseholdMember"]] = relationship("HouseholdMember", back_populates="household")


class HouseholdMember(Base):
    """
    Links a person to a household with dates.
    """
    __tablename__ = "household_members"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # When they lived there
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # NULL = current
    
    # Role in household
    is_head_of_household: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    household: Mapped["Household"] = relationship("Household", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="household_memberships")


class LifeEventType(str, enum.Enum):
    """Types of life events for genogram."""
    # Already covered by user fields
    BIRTH = "birth"
    DEATH = "death"
    ADOPTION = "adoption"
    
    # Relationship events
    MARRIAGE = "marriage"
    DIVORCE = "divorce"
    SEPARATION = "separation"
    ENGAGEMENT = "engagement"
    
    # Family events
    CHILD_BORN = "child_born"
    CHILD_ADOPTED = "child_adopted"
    GAINED_CUSTODY = "gained_custody"
    LOST_CUSTODY = "lost_custody"
    
    # Life transitions
    RELOCATION = "relocation"
    EDUCATION_START = "education_start"
    EDUCATION_COMPLETE = "education_complete"
    CAREER_START = "career_start"
    CAREER_CHANGE = "career_change"
    RETIREMENT = "retirement"
    
    # Health events
    DIAGNOSIS = "diagnosis"
    HOSPITALIZATION = "hospitalization"
    RECOVERY = "recovery"
    SURGERY = "surgery"
    
    # Legal events
    ARREST = "arrest"
    INCARCERATION = "incarceration"
    RELEASE = "release"
    
    # Other significant events
    MILITARY_SERVICE = "military_service"
    IMMIGRATION = "immigration"
    RELIGIOUS_EVENT = "religious_event"
    ACHIEVEMENT = "achievement"
    TRAUMA = "trauma"
    OTHER = "other"


class LifeEvent(Base):
    """
    Represents significant life events for genogram context.
    Extends the timeline system with genogram-specific events.
    """
    __tablename__ = "life_events"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    event_type: Mapped[LifeEventType] = mapped_column(SQLEnum(LifeEventType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # For ongoing events
    
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Link to other entities if applicable
    related_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)  # e.g., spouse in marriage
    related_partnership_id: Mapped[Optional[int]] = mapped_column(ForeignKey("partnerships.id"), nullable=True)
    
    # Privacy and display
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    show_on_genogram: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="life_events")
    related_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[related_user_id])


class MedicalCondition(Base):
    """
    Medical conditions, diagnoses, and health information for genogram.
    """
    __tablename__ = "medical_conditions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    condition_name: Mapped[str] = mapped_column(String(255), nullable=False)
    diagnosis_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    resolution_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # If cured/resolved
    
    is_genetic: Mapped[bool] = mapped_column(Boolean, default=False)
    is_chronic: Mapped[bool] = mapped_column(Boolean, default=False)
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # If this was cause of death
    is_cause_of_death: Mapped[bool] = mapped_column(Boolean, default=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Privacy
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="medical_conditions")
