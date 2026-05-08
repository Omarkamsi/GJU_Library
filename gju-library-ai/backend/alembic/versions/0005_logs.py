"""query_log, click_events, feedback_events

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-08

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "query_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("raw_query", sa.Text, nullable=False),
        sa.Column("lang", sa.String(8)),
        sa.Column("extracted_filters", postgresql.JSONB),
        sa.Column("retrieved_passage_ids", postgresql.ARRAY(sa.Integer)),
        sa.Column("shown_database_slugs", postgresql.ARRAY(sa.String)),
        sa.Column("answer_text", sa.Text),
        sa.Column("model_name", sa.String(64)),
        sa.Column("latency_ms", sa.Integer),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_query_log_user_created", "query_log", ["user_id", "created_at"])
    op.create_index("ix_query_log_created", "query_log", ["created_at"])

    op.create_table(
        "click_events",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("query_id", sa.Integer, sa.ForeignKey("query_log.id")),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_ref", sa.String(256)),
        sa.Column("target_url", sa.Text, nullable=False),
        sa.Column(
            "rendered_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("clicked_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index(
        "ix_click_target_clicked",
        "click_events",
        ["target_type", "target_ref", "clicked_at"],
    )
    op.create_index("ix_click_query", "click_events", ["query_id"])

    op.create_table(
        "feedback_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scope", sa.String(16), nullable=False),
        sa.Column("query_id", sa.Integer, sa.ForeignKey("query_log.id")),
        sa.Column("click_id", sa.String(32), sa.ForeignKey("click_events.id")),
        sa.Column("rating", sa.SmallInteger),
        sa.Column("comment", sa.Text),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("feedback_events")
    op.drop_index("ix_click_query", "click_events")
    op.drop_index("ix_click_target_clicked", "click_events")
    op.drop_table("click_events")
    op.drop_index("ix_query_log_created", "query_log")
    op.drop_index("ix_query_log_user_created", "query_log")
    op.drop_table("query_log")
