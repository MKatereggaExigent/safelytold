"""Create tenant-isolated investigation workflow tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'investigation_0001'
down_revision = None

def upgrade():
    common = lambda: [sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('status', sa.String(40), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)]
    op.create_table('investigations', *common(), sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('scope', sa.String(1000), nullable=False), sa.Column('issue_ids', sa.JSON(), nullable=False), sa.Column('evidence_sources', sa.JSON(), nullable=False), sa.Column('milestones', sa.JSON(), nullable=False))
    op.create_table('investigation_findings', *common(), sa.Column('investigation_id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('allegation_id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('category', sa.String(24), nullable=False), sa.Column('rationale_ref', sa.String(500), nullable=False), sa.Column('evidence_ids', sa.JSON(), nullable=False), sa.Column('contrary_evidence_ids', sa.JSON(), nullable=False), sa.Column('limitations', sa.JSON(), nullable=False), sa.Column('reviewer_approval_id', postgresql.UUID(as_uuid=True)))
    op.create_table('investigation_appeals', *common(), sa.Column('investigation_id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('grounds_ref', sa.String(500), nullable=False), sa.Column('reviewer_ref', sa.String(160), nullable=False), sa.Column('additional_evidence_ids', sa.JSON(), nullable=False), sa.Column('decided_at', sa.DateTime(timezone=True)))

def downgrade():
    for name in ('investigation_appeals', 'investigation_findings', 'investigations'):
        op.drop_table(name)
