"""Add text enhancement and duplicate detection fields

Revision ID: 003_text_enhancement
Revises: 002_initial_schema
Create Date: 2026-11-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_text_enhancement'
down_revision = '002_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Add new fields for text enhancement and duplicate detection"""
    
    # Add content hash for exact duplicate detection
    op.add_column('staging_submissions', 
        sa.Column('content_hash', sa.String(64), nullable=True)
    )
    op.create_index('ix_staging_submissions_content_hash', 
        'staging_submissions', ['content_hash']
    )
    
    # Add content fingerprint for near-duplicate detection (SimHash)
    op.add_column('staging_submissions', 
        sa.Column('content_fingerprint', sa.String(64), nullable=True)
    )
    op.create_index('ix_staging_submissions_content_fingerprint', 
        'staging_submissions', ['content_fingerprint']
    )
    
    # Add auto-extracted metadata (JSON)
    op.add_column('staging_submissions', 
        sa.Column('auto_extracted_metadata', sa.Text, nullable=True)
    )
    
    # Add enhancement changes log (JSON)
    op.add_column('staging_submissions', 
        sa.Column('enhancement_changes', sa.Text, nullable=True)
    )
    
    # Add text quality score
    op.add_column('staging_submissions', 
        sa.Column('text_quality_score', sa.Integer, nullable=True)
    )
    
    # Add detected risk level
    op.add_column('staging_submissions', 
        sa.Column('detected_risk_level', sa.String(10), nullable=True)
    )


def downgrade():
    """Remove text enhancement and duplicate detection fields"""
    
    # Drop indexes first
    op.drop_index('ix_staging_submissions_content_hash', 
        table_name='staging_submissions'
    )
    op.drop_index('ix_staging_submissions_content_fingerprint', 
        table_name='staging_submissions'
    )
    
    # Drop columns
    op.drop_column('staging_submissions', 'content_hash')
    op.drop_column('staging_submissions', 'content_fingerprint')
    op.drop_column('staging_submissions', 'auto_extracted_metadata')
    op.drop_column('staging_submissions', 'enhancement_changes')
    op.drop_column('staging_submissions', 'text_quality_score')
    op.drop_column('staging_submissions', 'detected_risk_level')
