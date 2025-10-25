"""Make email and password optional, add is_record_only flag

Revision ID: 0008
Revises: 0007
Create Date: 2025-10-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_record_only column with default False
    op.add_column('users', sa.Column('is_record_only', sa.Boolean(), nullable=False, server_default='0'))
    
    # Make email nullable (it's currently unique and not null)
    # First, we need to handle the existing constraint
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('email',
                              existing_type=sa.String(255),
                              nullable=True)
        batch_op.alter_column('password_hash',
                              existing_type=sa.String(255),
                              nullable=True)
    
    # Set is_record_only=True for any existing users without email or password
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE users SET is_record_only = 1 WHERE email IS NULL OR password_hash IS NULL"
    ))


def downgrade():
    # Set default email for any NULL emails before making it NOT NULL again
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE users SET email = CONCAT('user', id, '@example.com') WHERE email IS NULL"
    ))
    conn.execute(sa.text(
        "UPDATE users SET password_hash = 'disabled' WHERE password_hash IS NULL"
    ))
    
    # Revert columns to NOT NULL
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('email',
                              existing_type=sa.String(255),
                              nullable=False)
        batch_op.alter_column('password_hash',
                              existing_type=sa.String(255),
                              nullable=False)
    
    # Drop is_record_only column
    op.drop_column('users', 'is_record_only')
