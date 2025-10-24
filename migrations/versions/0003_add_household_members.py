"""add household_members for family tree

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-20

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the household_members table for user-based family tree
    op.create_table(
        "household_members",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("household_id", sa.Integer(), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.String(length=64), nullable=False),
        sa.Column("related_to_id", sa.Integer(), sa.ForeignKey("household_members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.String(length=512), nullable=True),
        sa.Column("joined_date", sa.Date(), nullable=True),
    )
    
    # Add unique constraint to prevent duplicate household memberships
    op.create_unique_constraint("uq_household_user", "household_members", ["household_id", "user_id"])


def downgrade() -> None:
    op.drop_constraint("uq_household_user", "household_members", type_="unique")
    op.drop_table("household_members")
