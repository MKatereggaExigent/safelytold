"""Initial schema for tenants, cases, reporter handles."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False, unique=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("region", sa.String(length=32), nullable=True),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("jurisdiction_code", sa.String(length=16), nullable=False),
        sa.Column("taxonomy_codes", postgresql.ARRAY(sa.String(length=64)), nullable=False),
        sa.Column("immediate_risk", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("questionnaire", postgresql.JSONB(), nullable=True),
        sa.Column("sealed_narrative", sa.Text(), nullable=False),
        sa.Column("narrative_length", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_cases_tenant_id", "cases", ["tenant_id"])

    op.create_table(
        "reporter_handles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("public_code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("secret_hash", sa.String(length=256), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_reporter_handles_public_code", "reporter_handles", ["public_code"], unique=True)


def downgrade() -> None:
    op.drop_table("reporter_handles")
    op.drop_table("cases")
    op.drop_table("tenants")
