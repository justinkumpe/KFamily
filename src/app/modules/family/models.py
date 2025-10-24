from __future__ import annotations

from datetime import date
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Integer, String, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...db import Base

if TYPE_CHECKING:
    from ..users.models import User


class Household(Base):
    __tablename__ = "households"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(64))
    email: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationship to household members
    members: Mapped[List["HouseholdMember"]] = relationship(
        "HouseholdMember", back_populates="household", cascade="all, delete-orphan"
    )

    # Non-member viewers (view-only access)
    viewers: Mapped[List["HouseholdViewer"]] = relationship(
        "HouseholdViewer", back_populates="household", cascade="all, delete-orphan"
    )


class HouseholdViewer(Base):
    """Grants view-only access to a household for non-members"""

    __tablename__ = "household_viewers"
    __table_args__ = (UniqueConstraint("household_id", "user_id", name="uq_household_viewer"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    granted_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    granted_date: Mapped[Optional[date]] = mapped_column(Date)

    # Relationships
    household: Mapped["Household"] = relationship("Household", back_populates="viewers")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    granted_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[granted_by_id])


class HouseholdMember(Base):
    """Links users to households with roles. Family relationships are defined in UserRelationship table."""

    __tablename__ = "household_members"
    __table_args__ = (UniqueConstraint("household_id", "user_id", name="uq_household_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Household role: determines what user can do with this household
    # - admin: full control (add/remove members, edit household, delete household)
    # - user: can view and edit household data, add members
    # - view-only: can only view household data
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="user")

    # Optional: additional notes about this household membership
    notes: Mapped[Optional[str]] = mapped_column(String(500))

    # Timestamps
    joined_date: Mapped[Optional[date]] = mapped_column(Date)

    # Relationships
    household: Mapped["Household"] = relationship("Household", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="household_memberships")


# Keep Person model for backward compatibility, but mark as deprecated
# Will be removed in future migration
class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    birthday: Mapped[Optional[date]] = mapped_column(Date)
    sex: Mapped[Optional[str]] = mapped_column(String(32))
    gender: Mapped[Optional[str]] = mapped_column(String(64))
    phone: Mapped[Optional[str]] = mapped_column(String(64))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    relation: Mapped[Optional[str]] = mapped_column(String(64))  # parent/child/adult/etc.

    household: Mapped[Household] = relationship("Household")

    @property
    def age(self) -> Optional[int]:
        if not self.birthday:
            return None
        today = date.today()
        years = (
            today.year
            - self.birthday.year
            - ((today.month, today.day) < (self.birthday.month, self.birthday.day))
        )
        return years


class UserRelationship(Base):
    """
    Direct family relationships between users, independent of household membership.
    Allows linking users as parent/child/sibling/etc without requiring them to be in the same household.
    """

    __tablename__ = "user_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    related_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationship type: parent, father, mother, adoptive-parent, adoptive-father, adoptive-mother,
    # child, son, daughter, spouse, sibling, brother, sister, grandparent, grandchild, etc.
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)

    notes: Mapped[Optional[str]] = mapped_column(String(512))
    created_date: Mapped[Optional[date]] = mapped_column(Date)

    # Relationships
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="family_relationships"
    )
    related_user: Mapped["User"] = relationship(
        "User", foreign_keys=[related_user_id], back_populates="related_to_me"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "related_user_id", "relationship_type", name="uq_user_relationship"
        ),
    )
