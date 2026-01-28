"""add_downloaded_files_table

Revision ID: bc0cea9ec17d
Revises: 16b7b7b50c3c
Create Date: 2026-01-28 15:48:07.446301

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc0cea9ec17d'
down_revision = '16b7b7b50c3c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'downloaded_files',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('source_hash', sa.String(length=64), nullable=False),
        sa.Column('standardized_filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('download_date', sa.DateTime(), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('chamber', sa.String(length=50), nullable=True),
        sa.Column('parliament_term', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_hash')
    )
    
    op.create_index('idx_downloaded_files_hash', 'downloaded_files', ['source_hash'])
    op.create_index('idx_downloaded_files_type', 'downloaded_files', ['document_type'])
    op.create_index('idx_downloaded_files_date', 'downloaded_files', ['download_date'])


def downgrade() -> None:
    op.drop_index('idx_downloaded_files_date', table_name='downloaded_files')
    op.drop_index('idx_downloaded_files_type', table_name='downloaded_files')
    op.drop_index('idx_downloaded_files_hash', table_name='downloaded_files')
    op.drop_table('downloaded_files')
