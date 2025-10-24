"""Remove relationship_type from household_members

Revision ID: 0007
Revises: 0006
Create Date: 2025-10-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    # Drop related_to_id foreign key constraint and column
    # This column is no longer needed as relationships are in user_relationships table
    try:
        op.drop_constraint('household_members_ibfk_3', 'household_members', type_='foreignkey')
    except Exception:
        pass  # Constraint might not exist
    
    # Check if columns exist before trying to drop them
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('household_members')]
    
    if 'related_to_id' in columns:
        op.drop_column('household_members', 'related_to_id')
    
    if 'relationship_type' in columns:
        op.drop_column('household_members', 'relationship_type')


def downgrade():
    # Add relationship_type column back
    op.add_column('household_members',
        sa.Column('relationship_type', sa.String(64), nullable=True)
    )
    
    # Add related_to_id column back
    op.add_column('household_members',
        sa.Column('related_to_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_household_members_related_to',
        'household_members', 'household_members',
        ['related_to_id'], ['id'],
        ondelete='SET NULL'
    )
