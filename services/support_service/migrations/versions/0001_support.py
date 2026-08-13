from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='support_0001';down_revision=None
def upgrade():
 op.create_table('support_directory',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('status',sa.String(40),nullable=False),sa.Column('jurisdiction_code',sa.String(12),nullable=False),sa.Column('category',sa.String(60),nullable=False),sa.Column('provider_name',sa.String(160),nullable=False),sa.Column('contact_route',sa.String(500),nullable=False),sa.Column('disclaimer',sa.String(500),nullable=False),sa.Column('verified_at',sa.DateTime(timezone=True),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
 op.create_table('support_referrals',sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('status',sa.String(40),nullable=False),sa.Column('case_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('directory_entry_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('consent_receipt_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('created_by',sa.String(160),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
def downgrade():op.drop_table('support_referrals');op.drop_table('support_directory')
