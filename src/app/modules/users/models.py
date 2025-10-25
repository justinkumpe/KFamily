from __future__ import annotations

from datetime import date
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Integer, String, Date, Table, Column, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...db import Base
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

if TYPE_CHECKING:
    from ..family.models import HouseholdMember, UserRelationship
    from ..timeline.models import TimelineEvent


user_group_table = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("user_id", "group_id", name="uq_user_group"),
)


class User(Base, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_record_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Personal information for family tree
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))

    # Contact information
    phone: Mapped[Optional[str]] = mapped_column(String(64))
    address: Mapped[Optional[str]] = mapped_column(String(512))

    # Life events
    birthday: Mapped[Optional[date]] = mapped_column(Date)
    death_date: Mapped[Optional[date]] = mapped_column(Date)
    adoption_date: Mapped[Optional[date]] = mapped_column(Date)

    # Additional identity information
    sex: Mapped[Optional[str]] = mapped_column(String(32))  # biological sex
    gender: Mapped[Optional[str]] = mapped_column(String(64))  # gender identity

    # Additional notes
    notes: Mapped[Optional[str]] = mapped_column(String(1000))

    # relationships
    groups: Mapped[List["Group"]] = relationship(
        "Group", secondary=user_group_table, back_populates="users"
    )
    household_memberships: Mapped[List["HouseholdMember"]] = relationship(
        "HouseholdMember", back_populates="user", cascade="all, delete-orphan"
    )

    # Direct family relationships (not tied to households)
    family_relationships: Mapped[List["UserRelationship"]] = relationship(
        "UserRelationship",
        foreign_keys="UserRelationship.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    related_to_me: Mapped[List["UserRelationship"]] = relationship(
        "UserRelationship",
        foreign_keys="UserRelationship.related_user_id",
        back_populates="related_user",
        cascade="all, delete-orphan",
    )
    
    # Timeline events
    timeline_events: Mapped[List["TimelineEvent"]] = relationship(
        "TimelineEvent",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="TimelineEvent.event_date.desc()",
    )

    # password helpers
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)
        # If password is being set and we have an email, mark as not record-only
        if self.email:
            self.is_record_only = False

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def can_login(self) -> bool:
        """Check if user has credentials to login (email and password)."""
        return not self.is_record_only and self.email is not None and self.password_hash is not None

    def gravatar_url(self, size: int = 80) -> str:
        """
        Generate Gravatar URL for user's email.
        Uses mystery person (mp) as default for users without email or with record-only accounts.

        Args:
            size: Image size in pixels (default 80)

        Returns:
            Gravatar URL string
        """
        import hashlib

        if self.email:
            # Create MD5 hash of lowercase email
            email_hash = hashlib.md5(self.email.lower().strip().encode("utf-8")).hexdigest()
        else:
            # Use a consistent hash for users without email (generates same mystery person)
            email_hash = hashlib.md5(f"user-{self.id}".encode("utf-8")).hexdigest()

        # Use mystery person (mp) as default, with size parameter
        return f"https://www.gravatar.com/avatar/{email_hash}?d=mp&s={size}"

    # family tree helpers
    @property
    def age(self) -> Optional[int]:
        """Calculate age from birthday. Returns None if no birthday or person is deceased."""
        if not self.birthday:
            return None
        if self.death_date:
            # Calculate age at death
            delta = self.death_date - self.birthday
            return delta.days // 365
        # Calculate current age
        today = date.today()
        delta = today - self.birthday
        return delta.days // 365

    # group helpers
    def has_group(self, name: str) -> bool:
        return any(g.name == name for g in self.groups)

    def has_any_group(self, *names: str) -> bool:
        s = set(names)
        return any(g.name in s for g in self.groups)

    # household role helpers (NEW system with admin/user/view-only roles)
    def get_household_role(self, household_id: int) -> Optional[str]:
        """Get user's role in a household (admin, user, view-only) or None if not a member."""
        for m in self.household_memberships:
            if m.household_id == household_id:
                return m.role
        return None

    def has_household_role(self, household_id: int, *roles: str) -> bool:
        """Check if user has any of the specified roles in the household."""
        user_role = self.get_household_role(household_id)
        return user_role in roles if user_role else False

    def can_view_household(self, household_id: int) -> bool:
        """Check if user can view a household (member with any role OR non-member viewer)."""
        # Check if member
        if self.get_household_role(household_id) is not None:
            return True
        # Check if non-member viewer (requires session query - will be checked in routes)
        return False

    def can_edit_household(self, household_id: int) -> bool:
        """Check if user can edit household data (admin or user role)."""
        return self.has_household_role(household_id, "admin", "user")

    def can_manage_household(self, household_id: int) -> bool:
        """Check if user can manage household (add/remove members, delete household - admin only)."""
        return self.has_household_role(household_id, "admin")

    # household parent helpers (LEGACY - deprecated, kept for backward compatibility)
    def is_parent_in_household(self, household_id: int) -> bool:
        """
        DEPRECATED: relationship_type removed from household_members.
        Use UserRelationship for family connections.
        Returns True if user has admin or user role in household.
        """
        return self.has_household_role(household_id, "admin", "user")

    def get_household_children_ids(self, household_id: int) -> set[int]:
        """
        DEPRECATED: relationship_type removed from household_members.
        Returns all user IDs from this household if user has admin/user role.
        """
        if not self.has_household_role(household_id, "admin", "user"):
            return set()
        # Return all user IDs from this household (requires session query)
        return set()

    def can_edit_household_member(self, target_user_id: int) -> bool:
        """Check if this user can edit the target user (if they're admin/user in shared household)."""
        # Check if both users are in the same household and this user has edit rights
        for membership in self.household_memberships:
            if self.can_edit_household(membership.household_id):
                # Check if target user is in this household
                household = membership.household
                target_member_ids = {m.user_id for m in household.members}
                if target_user_id in target_member_ids:
                    return True
        return False

    def can_edit_user(self, target_user_id: int) -> bool:
        """
        Check if this user can edit another user's profile.
        Returns True if ANY of the following:
        1. Editing own profile (self.id == target_user_id)
        2. Has 'admin' or 'super-admin' group
        3. Is household admin in a household where target is a member
        4. Is listed as target's parent in family relationships
        """
        # Can always edit own profile
        if self.id == target_user_id:
            return True

        # Admins can edit anyone
        if self.has_any_group("admin", "super-admin"):
            return True

        # Check if household admin for any of target's households
        if self.can_edit_household_member(target_user_id):
            return True

        # Check if this user is target's parent in family relationships
        for rel in self.family_relationships:
            if rel.related_user_id == target_user_id:
                if rel.relationship_type in [
                    "parent",
                    "father",
                    "mother",
                    "adoptive-parent",
                    "adoptive-father",
                    "adoptive-mother",
                ]:
                    return True

        return False

    def can_view_user(self, target_user_id: int) -> bool:
        """
        Check if this user can view another user's profile.
        Returns True if ANY of the following:
        1. Viewing own profile (self.id == target_user_id)
        2. Has 'admin' or 'super-admin' group (can view all)
        3. In same household as target user (any role including view-only)
        4. Has direct family relationship with target user (either direction)
        """
        # Can always view own profile
        if self.id == target_user_id:
            return True

        # Admins can view anyone
        if self.has_any_group("admin", "super-admin"):
            return True

        # Check if in same household (any role can view household members)
        for membership in self.household_memberships:
            household = membership.household
            target_member_ids = {m.user_id for m in household.members}
            if target_user_id in target_member_ids:
                return True

        # Check for direct family relationship (outgoing: this user -> target)
        for rel in self.family_relationships:
            if rel.related_user_id == target_user_id:
                return True

        # Check for direct family relationship (incoming: target -> this user)
        for rel in self.related_to_me:
            if rel.user_id == target_user_id:
                return True

        return False


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    # relationships
    users: Mapped[List[User]] = relationship(
        "User", secondary=user_group_table, back_populates="groups"
    )


INITIAL_GROUPS = [
    "user",
    "child",
    "admin",
    "parent",
    "adult",
    "banned",
    "locked",
    "no-access",
    "super-admin",
    "family-admin",
    "family-view",
    "family-editor",
]
