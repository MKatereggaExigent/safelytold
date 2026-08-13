from datetime import UTC,datetime
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import DateTime,String,select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped,mapped_column
from safelytold_common.auth import ContextDep
from safelytold_common.db import Base,OutboxEvent,TenantMixin,session,set_tenant
from safelytold_common.service import create_app
router=APIRouter(prefix='/v1/support',tags=['support'])
class Directory(TenantMixin,Base):
 __tablename__='support_directory';jurisdiction_code:Mapped[str]=mapped_column(String(12));category:Mapped[str]=mapped_column(String(60));provider_name:Mapped[str]=mapped_column(String(160));contact_route:Mapped[str]=mapped_column(String(500));disclaimer:Mapped[str]=mapped_column(String(500));verified_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
class Referral(TenantMixin,Base):
 __tablename__='support_referrals';case_id:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),index=True);directory_entry_id:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True));consent_receipt_id:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True));created_by:Mapped[str]=mapped_column(String(160))
class EntryIn(BaseModel):jurisdiction_code:str=Field(min_length=2,max_length=12);category:str=Field(min_length=2,max_length=60);provider_name:str=Field(min_length=2,max_length=160);contact_route:str=Field(min_length=3,max_length=500);disclaimer:str=Field(min_length=3,max_length=500)
class ReferralIn(BaseModel):case_id:UUID;directory_entry_id:UUID;consent_receipt_id:UUID
def permit(c):
 if not c.roles.intersection({'case_manager','support_coordinator','platform_super_admin'}):raise HTTPException(403,'Support role required')
@router.post('/directory',status_code=201)
async def add(body:EntryIn,c:ContextDep,db:AsyncSession=Depends(session)):
 permit(c);await set_tenant(db,c.tenant_id);row=Directory(tenant_id=c.tenant_id,status='verified',verified_at=datetime.now(UTC),**body.model_dump());db.add(row);await db.commit();await db.refresh(row);return row
@router.get('/directory')
async def directory(c:ContextDep,db:AsyncSession=Depends(session),jurisdiction_code:str|None=None):
 await set_tenant(db,c.tenant_id);q=select(Directory).where(Directory.tenant_id==c.tenant_id,Directory.status=='verified');q=q.where(Directory.jurisdiction_code==jurisdiction_code) if jurisdiction_code else q;return list(await db.scalars(q))
@router.post('/referrals',status_code=201)
async def refer(body:ReferralIn,c:ContextDep,db:AsyncSession=Depends(session)):
 permit(c);await set_tenant(db,c.tenant_id);entry=await db.get(Directory,body.directory_entry_id)
 if entry is None or entry.tenant_id!=c.tenant_id or entry.status!='verified':raise HTTPException(404,'Verified provider not found')
 row=Referral(tenant_id=c.tenant_id,status='created',created_by=c.subject_id,**body.model_dump());db.add(row);await db.flush();db.add(OutboxEvent(tenant_id=c.tenant_id,event_type='support.referral_created.v1',subject=f'case/{row.case_id}',payload={'case_id':str(row.case_id),'referral_id':str(row.id),'consent_receipt_id':str(row.consent_receipt_id)}));await db.commit();await db.refresh(row);return row
@router.get('/referrals')
async def referrals(c:ContextDep,db:AsyncSession=Depends(session),case_id:UUID|None=None):
 permit(c);await set_tenant(db,c.tenant_id);q=select(Referral).where(Referral.tenant_id==c.tenant_id);q=q.where(Referral.case_id==case_id) if case_id else q;return list(await db.scalars(q.order_by(Referral.created_at.desc())))
app=create_app('Support Service','Consent-referenced referrals to verified jurisdiction-specific providers.',[router])
