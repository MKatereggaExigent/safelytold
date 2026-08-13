from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='privacy_0001';down_revision=None
def common():return [sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('status',sa.String(40),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False)]
def upgrade():
 op.create_table('consent_receipts',*common(),sa.Column('subject_ref',sa.String(160),nullable=False),sa.Column('purpose',sa.String(240),nullable=False),sa.Column('notice_version',sa.String(40),nullable=False),sa.Column('decision',sa.String(20),nullable=False),sa.Column('recorded_at',sa.DateTime(timezone=True),nullable=False))
 op.create_table('data_subject_requests',*common(),sa.Column('request_type',sa.String(30),nullable=False),sa.Column('requester_ref',sa.String(160),nullable=False),sa.Column('identity_verification_ref',sa.String(240),nullable=False),sa.Column('scope',sa.JSON(),nullable=False),sa.Column('due_at',sa.DateTime(timezone=True),nullable=False),sa.Column('restrictions',sa.JSON(),nullable=False),sa.Column('decision_notes',sa.String(1000)))
 op.create_table('privacy_breaches',*common(),sa.Column('incident_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('jurisdictions',sa.JSON(),nullable=False),sa.Column('affected_data_classes',sa.JSON(),nullable=False),sa.Column('notification_decisions',sa.JSON(),nullable=False))
def downgrade():
 for table in ('privacy_breaches','data_subject_requests','consent_receipts'):op.drop_table(table)
