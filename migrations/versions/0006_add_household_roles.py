"""Add household roles and make relationship_type optional

Revision ID: 0006
Revises: 0005
Create Date: 2025-10-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    # Add role column to household_members
    op.add_column('household_members', 
        sa.Column('role', sa.String(64), nullable=False, server_default='user')
    )
    # Remove server_default after column is created
    op.alter_column('household_members', 'role', server_default=None)
    
    # Make relationship_type nullable (optional)
    op.alter_column('household_members', 'relationship_type',
        existing_type=sa.String(64),
        nullable=True
    )
    
    # Create household_viewers table for non-member view access
    op.create_table(
        'household_viewers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('household_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('granted_by_id', sa.Integer(), nullable=True),
        sa.Column('granted_date', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['household_id'], ['households.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('household_id', 'user_id', name='uq_household_viewer')
    )


def downgrade():
    # Drop household_viewers table
    op.drop_table('household_viewers')
    
    # Remove role column
    op.drop_column('household_members', 'role')
    
    # Make relationship_type non-nullable again
    op.alter_column('household_members', 'relationship_type',
        existing_type=sa.String(64),
        nullable=False
    )
