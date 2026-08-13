from datetime import UTC,datetime
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,EmailStr,Field
from sqlalchemy import DateTime,JSON,String,UniqueConstraint,select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped,mapped_column
from safelytold_common.auth import ContextDep
from safelytold_common.db import Base,OutboxEvent,TenantMixin,session,set_tenant
from safelytold_common.service import create_app
router=APIRouter(prefix='/v1/identity',tags=['identity'])
ALLOWED_ROLES={'case_manager','investigator','reviewer','decision_maker','privacy_officer','protection_officer','support_coordinator','auditor'}
ALLOWED_ACTIONS={'read','comment','assign','investigate','review','decide','export'}
class Identity(TenantMixin,Base):
 __tablename__='staff_identities';__table_args__=(UniqueConstraint('tenant_id','external_subject',name='uq_staff_subject'),);external_subject:Mapped[str]=mapped_column(String(160));roles:Mapped[list[str]]=mapped_column(JSON,default=list);organisational_unit_ids:Mapped[list[str]]=mapped_column(JSON,default=list)
class Invitation(TenantMixin,Base):
 __tablename__='scoped_invitations';email_commitment:Mapped[str]=mapped_column(String(64));case_id:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),index=True);role:Mapped[str]=mapped_column(String(40));expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True));created_by:Mapped[str]=mapped_column(String(160));redeemed_by:Mapped[str|None]=mapped_column(String(160))
class Grant(TenantMixin,Base):
 __tablename__='access_grants';subject_id:Mapped[str]=mapped_column(String(160),index=True);resource_id:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),index=True);actions:Mapped[list[str]]=mapped_column(JSON);purpose:Mapped[str]=mapped_column(String(240));approved_by:Mapped[list[str]]=mapped_column(JSON);valid_from:Mapped[datetime]=mapped_column(DateTime(timezone=True));valid_until:Mapped[datetime]=mapped_column(DateTime(timezone=True));revoked_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
class IdentityIn(BaseModel):external_subject:str=Field(min_length=2,max_length=160);roles:set[str]=Field(default_factory=set);organisational_unit_ids:set[UUID]=Field(default_factory=set)
class InviteIn(BaseModel):invitee_email:EmailStr;case_id:UUID;role:str;expires_at:datetime
class GrantIn(BaseModel):subject_id:str=Field(min_length=2,max_length=160);resource_id:UUID;actions:set[str]=Field(min_length=1);purpose:str=Field(min_length=3,max_length=240);approved_by:list[str]=Field(min_length=2);valid_from:datetime;valid_until:datetime
def admin(c):
 if not c.roles.intersection({'tenant_admin','platform_super_admin'}):raise HTTPException(403,'Tenant administrator role required')
def validate_role(role):
 if role not in ALLOWED_ROLES:raise HTTPException(422,'Unsupported role')
async def own(db,model,id,tenant):
 row=await db.get(model,id)
 if row is None or row.tenant_id!=tenant:raise HTTPException(404,'Not found')
 return row
@router.post('/staff',status_code=201)
async def staff(body:IdentityIn,c:ContextDep,db:AsyncSession=Depends(session)):
 admin(c);await set_tenant(db,c.tenant_id)
 if not body.roles<=ALLOWED_ROLES:raise HTTPException(422,'Unsupported role')
 row=Identity(tenant_id=c.tenant_id,status='active',external_subject=body.external_subject,roles=sorted(body.roles),organisational_unit_ids=sorted(str(x) for x in body.organisational_unit_ids));db.add(row);await db.commit();await db.refresh(row);return row
@router.get('/staff')
async def list_staff(c:ContextDep,db:AsyncSession=Depends(session)):
 admin(c);await set_tenant(db,c.tenant_id);return list(await db.scalars(select(Identity).where(Identity.tenant_id==c.tenant_id).order_by(Identity.created_at.desc())))
@router.post('/invitations',status_code=201)
async def invite(body:InviteIn,c:ContextDep,db:AsyncSession=Depends(session)):
 import hashlib
 admin(c);validate_role(body.role);await set_tenant(db,c.tenant_id)
 if body.expires_at<=datetime.now(UTC):raise HTTPException(422,'Invitation expiry must be future')
 commitment=hashlib.sha256(body.invitee_email.lower().encode()).hexdigest();row=Invitation(tenant_id=c.tenant_id,status='pending',email_commitment=commitment,case_id=body.case_id,role=body.role,expires_at=body.expires_at,created_by=c.subject_id);db.add(row);await db.commit();await db.refresh(row);return row
@router.get('/invitations')
async def invitations(c:ContextDep,db:AsyncSession=Depends(session)):
 admin(c);await set_tenant(db,c.tenant_id);return list(await db.scalars(select(Invitation).where(Invitation.tenant_id==c.tenant_id).order_by(Invitation.created_at.desc())))
@router.get('/grants')
async def grants(c:ContextDep,db:AsyncSession=Depends(session)):
 admin(c);await set_tenant(db,c.tenant_id);return list(await db.scalars(select(Grant).where(Grant.tenant_id==c.tenant_id).order_by(Grant.created_at.desc())))
@router.post('/grants',status_code=201)
async def grant(body:GrantIn,c:ContextDep,db:AsyncSession=Depends(session)):
 admin(c);await set_tenant(db,c.tenant_id)
 if not body.actions<=ALLOWED_ACTIONS or body.valid_until<=body.valid_from or len(set(body.approved_by))<2:raise HTTPException(422,'Grant requires allowed actions, valid dates and two distinct approvers')
 if c.subject_id in body.approved_by:raise HTTPException(409,'Requester cannot approve their own privileged grant')
 row=Grant(tenant_id=c.tenant_id,status='active',actions=sorted(body.actions),**body.model_dump(exclude={'actions'}));db.add(row);await db.flush();db.add(OutboxEvent(tenant_id=c.tenant_id,event_type='identity.access_granted.v1',subject=f'resource/{row.resource_id}',payload={'grant_id':str(row.id),'subject_id':row.subject_id,'actions':row.actions,'valid_until':row.valid_until.isoformat()}));await db.commit();await db.refresh(row);return row
@router.delete('/grants/{grant_id}',status_code=204)
async def revoke(grant_id:UUID,c:ContextDep,db:AsyncSession=Depends(session)):
 admin(c);await set_tenant(db,c.tenant_id);row=await own(db,Grant,grant_id,c.tenant_id);row.status='revoked';row.revoked_at=datetime.now(UTC);await db.commit()
@router.get('/grants/effective/{resource_id}')
async def effective(resource_id:UUID,c:ContextDep,db:AsyncSession=Depends(session)):
 await set_tenant(db,c.tenant_id);now=datetime.now(UTC);q=select(Grant).where(Grant.tenant_id==c.tenant_id,Grant.resource_id==resource_id,Grant.subject_id==c.subject_id,Grant.status=='active',Grant.valid_from<=now,Grant.valid_until>now);return list(await db.scalars(q))
app=create_app('Identity Service','Tenant identities, scoped invitations and dual-approved time-bound access grants.',[router])
