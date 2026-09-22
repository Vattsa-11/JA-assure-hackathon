"""add tracked_competitors

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-09-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tracked_competitors',
        sa.Column('competitor_url', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=False, server_default='manual'),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('competitor_url', name='uq_tracked_competitor_url'),
    )
    op.create_index('ix_tracked_competitors_competitor_url', 'tracked_competitors', ['competitor_url'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_tracked_competitors_competitor_url', table_name='tracked_competitors')
    op.drop_table('tracked_competitors')
