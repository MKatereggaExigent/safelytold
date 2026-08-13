from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='analytics_0001';down_revision=None
def upgrade():
 op.create_table('metric_observations',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('metric',sa.String(80),nullable=False),sa.Column('period',sa.Date(),nullable=False),sa.Column('dimensions',sa.JSON(),nullable=False),sa.Column('value',sa.Integer(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False));op.create_index('ix_metric_tenant_period','metric_observations',['tenant_id','metric','period'])
def downgrade():op.drop_index('ix_metric_tenant_period',table_name='metric_observations');op.drop_table('metric_observations')
