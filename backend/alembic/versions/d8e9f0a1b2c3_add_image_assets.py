"""add image_assets

Revision ID: d8e9f0a1b2c3
Revises: b7c8d9e0f1a2
Create Date: 2026-09-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8e9f0a1b2c3'
down_revision: Union[str, Sequence[str], None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('image_assets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('content_asset_id', sa.Integer(),
                  sa.ForeignKey('content_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('prompt', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('image_file_path', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='generated'),
    )
    op.create_index(op.f('ix_image_assets_id'), 'image_assets', ['id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_image_assets_id'), table_name='image_assets')
    op.drop_table('image_assets')
