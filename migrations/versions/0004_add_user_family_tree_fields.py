"""add user family tree fields

Revision ID: 0004
Revises: 0003
Create Date: 2025-10-21

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add family tree fields to users table
    op.add_column("users", sa.Column("first_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("middle_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("address", sa.String(length=512), nullable=True))
    op.add_column("users", sa.Column("birthday", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("death_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("adoption_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("sex", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("gender", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("notes", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "notes")
    op.drop_column("users", "gender")
    op.drop_column("users", "sex")
    op.drop_column("users", "adoption_date")
    op.drop_column("users", "death_date")
    op.drop_column("users", "birthday")
    op.drop_column("users", "address")
    op.drop_column("users", "phone")
    op.drop_column("users", "last_name")
    op.drop_column("users", "middle_name")
    op.drop_column("users", "first_name")
