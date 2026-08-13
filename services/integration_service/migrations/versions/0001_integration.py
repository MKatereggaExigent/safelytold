from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='integration_0001';down_revision=None
def upgrade():
 op.create_table('operational_records',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('area',sa.String(40),nullable=False),sa.Column('status',sa.String(40),nullable=False),sa.Column('idempotency_key',sa.String(160),nullable=False),sa.Column('payload',sa.JSON(),nullable=False),sa.Column('created_by',sa.String(160),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint('tenant_id','area','idempotency_key',name='uq_operational_idempotency'))
def downgrade():op.drop_table('operational_records')
