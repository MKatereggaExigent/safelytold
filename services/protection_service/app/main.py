from datetime import UTC, datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, JSON, String, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from safelytold_common.auth import ContextDep
from safelytold_common.db import Base, OutboxEvent, TenantMixin, session, set_tenant
from safelytold_common.service import create_app

router=APIRouter(prefix='/v1/protection',tags=['protection'])
class Plan(TenantMixin,Base):
 __tablename__='protection_plans';case_id:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),index=True);requested_measures:Mapped[list[str]]=mapped_column(JSON);approved_measures:Mapped[list[str]]=mapped_column(JSON);owner_ref:Mapped[str]=mapped_column(String(160));next_review_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
class CheckIn(TenantMixin,Base):
 __tablename__='retaliation_checkins';case_id:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),index=True);due_at:Mapped[datetime]=mapped_column(DateTime(timezone=True));completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True));risk_band:Mapped[str|None]=mapped_column(String(20));notes:Mapped[list[str]]=mapped_column(JSON,default=list);escalation_id:Mapped[UUID|None]=mapped_column(PGUUID(as_uuid=True))
class PlanIn(BaseModel):
 case_id:UUID;requested_measures:list[str]=Field(min_length=1,max_length=30);approved_measures:list[str]=Field(min_length=1,max_length=30);owner_ref:str=Field(min_length=1,max_length=160);next_review_at:datetime
class CheckInIn(BaseModel):due_at:datetime
class Complete(BaseModel):risk_band:str=Field(pattern='^(low|medium|high|critical)$');notes:list[str]=Field(default_factory=list,max_length=30);escalation_id:UUID|None=None
def permit(c):
 if not c.roles.intersection({'case_manager','protection_officer','platform_super_admin'}):raise HTTPException(403,'Protection role required')
async def own(db,model,id,tenant):
 row=await db.get(model,id)
 if row is None or row.tenant_id!=tenant:raise HTTPException(404,'Not found')
 return row
@router.post('/plans',status_code=201)
async def plan(body:PlanIn,c:ContextDep,db:AsyncSession=Depends(session)):
 permit(c);await set_tenant(db,c.tenant_id)
 if body.next_review_at<=datetime.now(UTC) or not set(body.approved_measures)<=set(body.requested_measures):raise HTTPException(422,'Review must be future and approved measures must be requested')
 row=Plan(tenant_id=c.tenant_id,status='active',**body.model_dump());db.add(row);await db.flush();db.add(OutboxEvent(tenant_id=c.tenant_id,event_type='protection.plan_activated.v1',subject=f'case/{row.case_id}',payload={'case_id':str(row.case_id),'plan_id':str(row.id)}));await db.commit();await db.refresh(row);return row
@router.post('/plans/{plan_id}/check-ins',status_code=201)
async def schedule(plan_id:UUID,body:CheckInIn,c:ContextDep,db:AsyncSession=Depends(session)):
 permit(c);await set_tenant(db,c.tenant_id);p=await own(db,Plan,plan_id,c.tenant_id)
 if p.status!='active' or body.due_at<=datetime.now(UTC):raise HTTPException(409,'Active plan and future due date required')
 row=CheckIn(tenant_id=c.tenant_id,status='scheduled',case_id=p.case_id,due_at=body.due_at);db.add(row);await db.commit();await db.refresh(row);return row
@router.post('/check-ins/{check_id}/complete')
async def complete(check_id:UUID,body:Complete,c:ContextDep,db:AsyncSession=Depends(session)):
 permit(c);await set_tenant(db,c.tenant_id);row=await own(db,CheckIn,check_id,c.tenant_id)
 if row.status!='scheduled':raise HTTPException(409,'Check-in already completed')
 if body.risk_band in {'high','critical'} and body.escalation_id is None:raise HTTPException(422,'High-risk check-ins require an escalation')
 row.status='completed';row.completed_at=datetime.now(UTC);row.risk_band=body.risk_band;row.notes=body.notes;row.escalation_id=body.escalation_id;db.add(OutboxEvent(tenant_id=c.tenant_id,event_type='protection.checkin_completed.v1',subject=f'case/{row.case_id}',payload={'case_id':str(row.case_id),'risk_band':row.risk_band,'escalation_id':str(row.escalation_id) if row.escalation_id else None}));await db.commit();return row
@router.get('/case/{case_id}')
async def by_case(case_id:UUID,c:ContextDep,db:AsyncSession=Depends(session)):
 await set_tenant(db,c.tenant_id);return list(await db.scalars(select(Plan).where(Plan.tenant_id==c.tenant_id,Plan.case_id==case_id)))
@router.get('/check-ins')
async def checkins(c:ContextDep,db:AsyncSession=Depends(session),case_id:UUID|None=None):
 permit(c);await set_tenant(db,c.tenant_id);q=select(CheckIn).where(CheckIn.tenant_id==c.tenant_id);q=q.where(CheckIn.case_id==case_id) if case_id else q;return list(await db.scalars(q.order_by(CheckIn.due_at)))
app=create_app('Protection Service','Anti-retaliation plans, scheduled monitoring and mandatory risk escalation.',[router])
