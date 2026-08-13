"""Create tenant-isolated case workflow tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'case_0001'
down_revision = None

def upgrade():
    common = [sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True), sa.Column('status', sa.String(40), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)]
    op.create_table('cases', *common, sa.Column('public_reference', sa.String(32), nullable=False), sa.Column('jurisdiction_code', sa.String(12), nullable=False), sa.Column('severity_band', sa.String(20), nullable=False), sa.Column('workflow_id', sa.String(80), nullable=False), sa.Column('policy_version_id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('closed_at', sa.DateTime(timezone=True)), sa.UniqueConstraint('tenant_id', 'public_reference', name='uq_case_reference'))
    for name, columns in (
        ('case_allegations', [sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('taxonomy_code', sa.String(80), nullable=False)]),
        ('case_conflict_checks', [sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('candidate_subject_id', sa.String(160), nullable=False), sa.Column('conflicts', sa.JSON(), nullable=False), sa.Column('decision', sa.String(20), nullable=False), sa.Column('reviewed_by', sa.String(160), nullable=False)]),
        ('case_assignments', [sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('subject_id', sa.String(160), nullable=False), sa.Column('role', sa.String(40), nullable=False), sa.Column('purpose', sa.String(240), nullable=False), sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False), sa.Column('conflict_check_id', postgresql.UUID(as_uuid=True), nullable=False)]),
    ):
        op.create_table(name, *[c.copy() for c in common], *columns)

def downgrade():
    for name in ('case_assignments', 'case_conflict_checks', 'case_allegations', 'cases'):
        op.drop_table(name)
