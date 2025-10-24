"""add user_relationships table for direct family links

Revision ID: 0005
Revises: 0004
Create Date: 2025-10-21

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_relationships table for direct family links (independent of households)
    op.create_table(
        "user_relationships",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("related_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.String(length=512), nullable=True),
        sa.Column("created_date", sa.Date(), nullable=True),
    )
    
    # Add unique constraint to prevent duplicate relationships
    op.create_unique_constraint("uq_user_relationship", "user_relationships", ["user_id", "related_user_id", "relationship_type"])
    
    # Add index for reverse lookups
    op.create_index("idx_related_user", "user_relationships", ["related_user_id"])


def downgrade() -> None:
    op.drop_index("idx_related_user", "user_relationships")
    op.drop_constraint("uq_user_relationship", "user_relationships", type_="unique")
    op.drop_table("user_relationships")
