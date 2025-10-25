"""Add timeline_events table

Revision ID: 0009
Revises: 0008
Create Date: 2025-10-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    # Create timeline_events table
    op.create_table(
        'timeline_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('module_name', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('visibility', sa.String(length=20), nullable=False, server_default='private'),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('is_auto_generated', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_timeline_events_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_timeline_events_user_id', 'timeline_events', ['user_id'])
    op.create_index('ix_timeline_events_event_date', 'timeline_events', ['event_date'])
    op.create_index('ix_timeline_events_module_name', 'timeline_events', ['module_name'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_timeline_events_module_name', 'timeline_events')
    op.drop_index('ix_timeline_events_event_date', 'timeline_events')
    op.drop_index('ix_timeline_events_user_id', 'timeline_events')
    
    # Drop table
    op.drop_table('timeline_events')
