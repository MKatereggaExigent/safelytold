from datetime import UTC,datetime,timedelta
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import DateTime,JSON,String,select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped,mapped_column
from safelytold_common.auth import ContextDep
from safelytold_common.db import Base,OutboxEvent,TenantMixin,session,set_tenant
from safelytold_common.service import create_app
router=APIRouter(prefix='/v1/privacy',tags=['privacy'])
class Consent(TenantMixin,Base):
 __tablename__='consent_receipts';subject_ref:Mapped[str]=mapped_column(String(160));purpose:Mapped[str]=mapped_column(String(240));notice_version:Mapped[str]=mapped_column(String(40));decision:Mapped[str]=mapped_column(String(20));recorded_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
class DSR(TenantMixin,Base):
 __tablename__='data_subject_requests';request_type:Mapped[str]=mapped_column(String(30));requester_ref:Mapped[str]=mapped_column(String(160));identity_verification_ref:Mapped[str]=mapped_column(String(240));scope:Mapped[list[str]]=mapped_column(JSON);due_at:Mapped[datetime]=mapped_column(DateTime(timezone=True));restrictions:Mapped[list[str]]=mapped_column(JSON,default=list);decision_notes:Mapped[str|None]=mapped_column(String(1000))
class Breach(TenantMixin,Base):
 __tablename__='privacy_breaches';incident_id:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True));jurisdictions:Mapped[list[str]]=mapped_column(JSON);affected_data_classes:Mapped[list[str]]=mapped_column(JSON);notification_decisions:Mapped[list[dict]]=mapped_column(JSON,default=list)
class ConsentIn(BaseModel):subject_ref:str=Field(min_length=1,max_length=160);purpose:str=Field(min_length=3,max_length=240);notice_version:str=Field(min_length=1,max_length=40);decision:str=Field(pattern='^(granted|denied|withdrawn)$')
class DSRIn(BaseModel):request_type:str=Field(pattern='^(access|correction|deletion|restriction|objection|portability)$');requester_ref:str=Field(min_length=1,max_length=160);identity_verification_ref:str=Field(min_length=3,max_length=240);scope:list[str]=Field(min_length=1,max_length=50);jurisdiction_code:str=Field(default='ZA',min_length=2,max_length=12)
class Decide(BaseModel):status:str=Field(pattern='^(fulfilled|partially_fulfilled|denied)$');decision_notes:str=Field(min_length=3,max_length=1000);restrictions:list[str]=Field(default_factory=list)
class BreachIn(BaseModel):incident_id:UUID;jurisdictions:list[str]=Field(min_length=1);affected_data_classes:list[str]=Field(min_length=1)
def permit(c):
 if not c.roles.intersection({'privacy_officer','platform_super_admin'}):raise HTTPException(403,'Privacy officer role required')
async def own(db,model,id,tenant):
 row=await db.get(model,id)
 if row is None or row.tenant_id!=tenant:raise HTTPException(404,'Not found')
 return row
@router.post('/consents',status_code=201)
async def consent(body:ConsentIn,c:ContextDep,db:AsyncSession=Depends(session)):
 await set_tenant(db,c.tenant_id);row=Consent(tenant_id=c.tenant_id,status='recorded',recorded_at=datetime.now(UTC),**body.model_dump());db.add(row);await db.commit();await db.refresh(row);return row
@router.get('/consents')
async def consents(c:ContextDep,db:AsyncSession=Depends(session)):
 permit(c);await set_tenant(db,c.tenant_id);return list(await db.scalars(select(Consent).where(Consent.tenant_id==c.tenant_id).order_by(Consent.recorded_at.desc())))
@router.post('/requests',status_code=201)
async def request(body:DSRIn,c:ContextDep,db:AsyncSession=Depends(session)):
 await set_tenant(db,c.tenant_id);days=30 if body.jurisdiction_code=='ZA' else 30;data=body.model_dump(exclude={'jurisdiction_code'});row=DSR(tenant_id=c.tenant_id,status='verified',due_at=datetime.now(UTC)+timedelta(days=days),**data);db.add(row);await db.flush();db.add(OutboxEvent(tenant_id=c.tenant_id,event_type='privacy.request_received.v1',subject=f'privacy/{row.id}',payload={'request_id':str(row.id),'type':row.request_type,'due_at':row.due_at.isoformat()}));await db.commit();await db.refresh(row);return row
@router.get('/requests')
async def requests(c:ContextDep,db:AsyncSession=Depends(session)):
 permit(c);await set_tenant(db,c.tenant_id);return list(await db.scalars(select(DSR).where(DSR.tenant_id==c.tenant_id).order_by(DSR.due_at)))
@router.post('/requests/{request_id}/decision')
async def decide(request_id:UUID,body:Decide,c:ContextDep,db:AsyncSession=Depends(session)):
 permit(c);await set_tenant(db,c.tenant_id);row=await own(db,DSR,request_id,c.tenant_id)
 if row.status not in {'verified','in_progress'}:raise HTTPException(409,'Request already decided')
 row.status=body.status;row.decision_notes=body.decision_notes;row.restrictions=body.restrictions;await db.commit();return row
@router.post('/breaches',status_code=201)
async def breach(body:BreachIn,c:ContextDep,db:AsyncSession=Depends(session)):
 permit(c);await set_tenant(db,c.tenant_id);row=Breach(tenant_id=c.tenant_id,status='assessing',notification_decisions=[],**body.model_dump());db.add(row);await db.flush();db.add(OutboxEvent(tenant_id=c.tenant_id,event_type='privacy.breach_opened.v1',subject=f'incident/{row.incident_id}',payload={'breach_id':str(row.id),'jurisdictions':row.jurisdictions}));await db.commit();await db.refresh(row);return row
@router.get('/breaches')
async def breaches(c:ContextDep,db:AsyncSession=Depends(session)):
 permit(c);await set_tenant(db,c.tenant_id);return list(await db.scalars(select(Breach).where(Breach.tenant_id==c.tenant_id).order_by(Breach.created_at.desc())))
app=create_app('Privacy Service','Consent receipts, statutory data-subject deadlines and breach assessment.',[router])
