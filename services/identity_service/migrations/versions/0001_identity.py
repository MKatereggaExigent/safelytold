from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='identity_0001';down_revision=None
def base():return [sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('status',sa.String(40),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False)]
def upgrade():
 op.create_table('staff_identities',*base(),sa.Column('external_subject',sa.String(160),nullable=False),sa.Column('roles',sa.JSON(),nullable=False),sa.Column('organisational_unit_ids',sa.JSON(),nullable=False),sa.UniqueConstraint('tenant_id','external_subject',name='uq_staff_subject'))
 op.create_table('scoped_invitations',*base(),sa.Column('email_commitment',sa.String(64),nullable=False),sa.Column('case_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('role',sa.String(40),nullable=False),sa.Column('expires_at',sa.DateTime(timezone=True),nullable=False),sa.Column('created_by',sa.String(160),nullable=False),sa.Column('redeemed_by',sa.String(160)))
 op.create_table('access_grants',*base(),sa.Column('subject_id',sa.String(160),nullable=False),sa.Column('resource_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('actions',sa.JSON(),nullable=False),sa.Column('purpose',sa.String(240),nullable=False),sa.Column('approved_by',sa.JSON(),nullable=False),sa.Column('valid_from',sa.DateTime(timezone=True),nullable=False),sa.Column('valid_until',sa.DateTime(timezone=True),nullable=False),sa.Column('revoked_at',sa.DateTime(timezone=True)))
def downgrade():
 for t in ('access_grants','scoped_invitations','staff_identities'):op.drop_table(t)
