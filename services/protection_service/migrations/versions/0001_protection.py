from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='protection_0001';down_revision=None
def upgrade():
 op.create_table('protection_plans',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('status',sa.String(40),nullable=False),sa.Column('case_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('requested_measures',sa.JSON(),nullable=False),sa.Column('approved_measures',sa.JSON(),nullable=False),sa.Column('owner_ref',sa.String(160),nullable=False),sa.Column('next_review_at',sa.DateTime(timezone=True),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
 op.create_table('retaliation_checkins',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('status',sa.String(40),nullable=False),sa.Column('case_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('due_at',sa.DateTime(timezone=True),nullable=False),sa.Column('completed_at',sa.DateTime(timezone=True)),sa.Column('risk_band',sa.String(20)),sa.Column('notes',sa.JSON(),nullable=False),sa.Column('escalation_id',postgresql.UUID(as_uuid=True)),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
def downgrade():op.drop_table('retaliation_checkins');op.drop_table('protection_plans')
