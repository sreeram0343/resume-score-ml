"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-06-02 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('resumes',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('file_type', sa.String(length=10), nullable=False),
    sa.Column('file_size_bytes', sa.Integer(), nullable=False),
    sa.Column('raw_text', sa.Text(), nullable=False),
    sa.Column('word_count', sa.Integer(), nullable=False),
    sa.Column('page_count', sa.Integer(), nullable=False),
    sa.Column('contact_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('sections', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ats_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('parsing_warnings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_resumes_created_at', 'resumes', ['created_at'], unique=False)
    
    op.create_table('scores',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('resume_id', sa.String(length=36), nullable=False),
    sa.Column('overall_score', sa.Float(), nullable=False),
    sa.Column('ats_score', sa.Float(), nullable=False),
    sa.Column('content_score', sa.Float(), nullable=False),
    sa.Column('keyword_score', sa.Float(), nullable=False),
    sa.Column('semantic_score', sa.Float(), nullable=False),
    sa.Column('grade', sa.String(length=3), nullable=False),
    sa.Column('job_description', sa.Text(), nullable=True),
    sa.Column('target_role', sa.String(length=100), nullable=True),
    sa.Column('feature_vector', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('shap_values', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('suggestions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('keyword_gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('waterfall_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('processing_time_ms', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scores_resume_id_created', 'scores', ['resume_id', 'created_at'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_scores_resume_id_created', table_name='scores')
    op.drop_table('scores')
    op.drop_index('ix_resumes_created_at', table_name='resumes')
    op.drop_table('resumes')
