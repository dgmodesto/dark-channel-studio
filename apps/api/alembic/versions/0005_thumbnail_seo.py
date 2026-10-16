"""add thumbnail and SEO data to review items

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"


def upgrade() -> None:
    op.add_column(
        "review_item",
        sa.Column("thumbnail_key", sa.String(512), nullable=False, server_default=""),
    )
    op.add_column(
        "review_item",
        sa.Column("description", sa.String(5000), nullable=False, server_default=""),
    )
    op.add_column(
        "review_item",
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "review_item",
        sa.Column(
            "synthetic_content_disclosed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("review_item", "synthetic_content_disclosed")
    op.drop_column("review_item", "tags")
    op.drop_column("review_item", "description")
    op.drop_column("review_item", "thumbnail_key")
