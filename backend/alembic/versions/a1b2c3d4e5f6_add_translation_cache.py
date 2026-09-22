"""add translation_cache

Revision ID: a1b2c3d4e5f6
Revises: c4f156fe2bc8
Create Date: 2026-09-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c4f156fe2bc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('translation_cache',
        sa.Column('source_hash', sa.String(length=64), nullable=False),
        sa.Column('target_language', sa.String(length=8), nullable=False),
        sa.Column('source_text', sa.String(), nullable=False),
        sa.Column('translated_text', sa.String(), nullable=False),
        sa.Column('hit_count', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_hash', 'target_language', name='uq_translation_hash_lang'),
    )
    op.create_index('ix_translation_cache_source_hash', 'translation_cache', ['source_hash'], unique=False)
    op.create_index('ix_translation_cache_target_language', 'translation_cache', ['target_language'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_translation_cache_target_language', table_name='translation_cache')
    op.drop_index('ix_translation_cache_source_hash', table_name='translation_cache')
    op.drop_table('translation_cache')
