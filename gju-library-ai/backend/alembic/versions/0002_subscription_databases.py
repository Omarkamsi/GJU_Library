"""subscription_databases

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-08

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscription_databases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("vendor", sa.String(200)),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("content_types", postgresql.ARRAY(sa.String)),
        sa.Column("subjects", postgresql.ARRAY(sa.String)),
        sa.Column("languages", postgresql.ARRAY(sa.String)),
        sa.Column("access_method", sa.String(64)),
        sa.Column("description_en", sa.Text),
        sa.Column("description_ar", sa.Text),
        sa.Column("description_de", sa.Text),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_sub_db_subjects",
        "subscription_databases",
        ["subjects"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_sub_db_subjects", "subscription_databases")
    op.drop_table("subscription_databases")
