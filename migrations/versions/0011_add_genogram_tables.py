"""Add genogram tables: partnerships, households, life_events, medical_conditions

Revision ID: 0011
Revises: 0010
Create Date: 2025-10-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade():
    # Check if partnerships table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create partnerships table
    if 'partnerships' not in existing_tables:
        op.create_table(
        'partnerships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('person1_id', sa.Integer(), nullable=False),
        sa.Column('person2_id', sa.Integer(), nullable=False),
        sa.Column('relationship_type', sa.Enum('MARRIED', 'DIVORCED', 'SEPARATED', 'COMMON_LAW', 'ENGAGED', 'DATING', 'FORMER_PARTNER', 'WIDOWED', name='relationshiptype'), nullable=False),
        sa.Column('relationship_quality', sa.Enum('CLOSE', 'VERY_CLOSE', 'DISTANT', 'ESTRANGED', 'CONFLICTED', 'ABUSIVE', 'NORMAL', name='relationshipquality'), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('has_children', sa.Boolean(), nullable=False, default=False),
        sa.Column('custody_type', sa.Enum('SOLE_MOTHER', 'SOLE_FATHER', 'JOINT', 'SPLIT', 'PRIMARY_MOTHER', 'PRIMARY_FATHER', 'OTHER_GUARDIAN', name='custodytype'), nullable=True),
        sa.Column('custody_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['person1_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['person2_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
        op.create_index(op.f('ix_partnerships_person1_id'), 'partnerships', ['person1_id'], unique=False)
        op.create_index(op.f('ix_partnerships_person2_id'), 'partnerships', ['person2_id'], unique=False)

    # Note: households and household_members tables already exist from previous migrations
    # and are defined in models.py, so we don't create them here.

    # Create life_events table
    if 'life_events' not in existing_tables:
        op.create_table(
            'life_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('event_type', sa.Enum(
                'BIRTH', 'DEATH', 'ADOPTION', 'MARRIAGE', 'DIVORCE', 'SEPARATION', 'ENGAGEMENT',
                'CHILD_BORN', 'CHILD_ADOPTED', 'GAINED_CUSTODY', 'LOST_CUSTODY',
                'RELOCATION', 'EDUCATION_START', 'EDUCATION_COMPLETE', 'CAREER_START', 'CAREER_CHANGE', 'RETIREMENT',
                'DIAGNOSIS', 'HOSPITALIZATION', 'RECOVERY', 'SURGERY',
                'ARREST', 'INCARCERATION', 'RELEASE',
                'MILITARY_SERVICE', 'IMMIGRATION', 'RELIGIOUS_EVENT', 'ACHIEVEMENT', 'TRAUMA', 'OTHER',
                name='lifeeventtype'
            ), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('event_date', sa.Date(), nullable=False),
            sa.Column('end_date', sa.Date(), nullable=True),
            sa.Column('location', sa.String(length=255), nullable=True),
            sa.Column('related_user_id', sa.Integer(), nullable=True),
            sa.Column('related_partnership_id', sa.Integer(), nullable=True),
            sa.Column('is_private', sa.Boolean(), nullable=False, default=False),
            sa.Column('show_on_genogram', sa.Boolean(), nullable=False, default=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['related_user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['related_partnership_id'], ['partnerships.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_life_events_user_id'), 'life_events', ['user_id'], unique=False)
        op.create_index(op.f('ix_life_events_event_date'), 'life_events', ['event_date'], unique=False)

    # Create medical_conditions table
    if 'medical_conditions' not in existing_tables:
        op.create_table(
            'medical_conditions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('condition_name', sa.String(length=255), nullable=False),
            sa.Column('diagnosis_date', sa.Date(), nullable=True),
            sa.Column('resolution_date', sa.Date(), nullable=True),
            sa.Column('is_genetic', sa.Boolean(), nullable=False, default=False),
            sa.Column('is_chronic', sa.Boolean(), nullable=False, default=False),
            sa.Column('is_terminal', sa.Boolean(), nullable=False, default=False),
            sa.Column('is_cause_of_death', sa.Boolean(), nullable=False, default=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('is_private', sa.Boolean(), nullable=False, default=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_medical_conditions_user_id'), 'medical_conditions', ['user_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_medical_conditions_user_id'), table_name='medical_conditions')
    op.drop_table('medical_conditions')
    
    op.drop_index(op.f('ix_life_events_event_date'), table_name='life_events')
    op.drop_index(op.f('ix_life_events_user_id'), table_name='life_events')
    op.drop_table('life_events')
    
    # Note: household_members and households tables are not dropped as they existed before this migration
    
    op.drop_index(op.f('ix_partnerships_person2_id'), table_name='partnerships')
    op.drop_index(op.f('ix_partnerships_person1_id'), table_name='partnerships')
    op.drop_table('partnerships')
    
    # Drop enum types
    sa.Enum(name='custodytype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='relationshipquality').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='relationshiptype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='lifeeventtype').drop(op.get_bind(), checkfirst=True)
