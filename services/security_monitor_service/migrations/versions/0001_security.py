from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='security_0001';down_revision=None
def upgrade():
 op.create_table('security_alerts',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('status',sa.String(40),nullable=False),sa.Column('alert_type',sa.String(80),nullable=False),sa.Column('severity',sa.String(20),nullable=False),sa.Column('resource_ref',sa.String(240),nullable=False),sa.Column('detected_at',sa.DateTime(timezone=True),nullable=False),sa.Column('privacy_safe_context',sa.JSON(),nullable=False),sa.Column('runbook',sa.String(160)),sa.Column('containment_actions',sa.JSON(),nullable=False),sa.Column('acknowledged_by',sa.String(160)),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
def downgrade():op.drop_table('security_alerts')
