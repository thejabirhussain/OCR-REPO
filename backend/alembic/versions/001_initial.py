"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(512), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('extraction_stage', sa.String(50), nullable=False),
        sa.Column('ocr_stage', sa.String(50), nullable=False),
        sa.Column('translation_stage', sa.String(50), nullable=False),
        sa.Column('arabic_json_path', sa.String(512), nullable=True),
        sa.Column('english_json_path', sa.String(512), nullable=True),
        sa.Column('arabic_json', postgresql.JSON, nullable=True),
        sa.Column('english_json', postgresql.JSON, nullable=True),
        sa.Column('stats', postgresql.JSON, nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('config', postgresql.JSON, nullable=True),
    )


def downgrade() -> None:
    op.drop_table('jobs')




