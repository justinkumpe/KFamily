"""Rename metadata to event_metadata in timeline_events

Revision ID: 0010
Revises: 0009
Create Date: 2025-10-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade():
    # Rename metadata column to event_metadata
    with op.batch_alter_table('timeline_events') as batch_op:
        batch_op.alter_column('metadata',
                              new_column_name='event_metadata',
                              existing_type=sa.JSON(),
                              existing_nullable=True)


def downgrade():
    # Rename event_metadata back to metadata
    with op.batch_alter_table('timeline_events') as batch_op:
        batch_op.alter_column('event_metadata',
                              new_column_name='metadata',
                              existing_type=sa.JSON(),
                              existing_nullable=True)
