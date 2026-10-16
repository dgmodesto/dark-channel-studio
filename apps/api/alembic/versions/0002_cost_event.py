"""cost_event table

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade() -> None:
    op.create_table(
        "cost_event",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("channel_id", sa.String(64), nullable=True),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("characters", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(12, 6), nullable=False),
        sa.Column("priced", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_cost_event_run_id", "cost_event", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_cost_event_run_id", table_name="cost_event")
    op.drop_table("cost_event")
