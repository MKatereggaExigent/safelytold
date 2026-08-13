from datetime import UTC,datetime
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
router=APIRouter(prefix='/v1/security',tags=['security-monitoring'])
class Alert(TenantMixin,Base):
 __tablename__='security_alerts';alert_type:Mapped[str]=mapped_column(String(80));severity:Mapped[str]=mapped_column(String(20));resource_ref:Mapped[str]=mapped_column(String(240));detected_at:Mapped[datetime]=mapped_column(DateTime(timezone=True));privacy_safe_context:Mapped[dict]=mapped_column(JSON,default=dict);runbook:Mapped[str|None]=mapped_column(String(160));containment_actions:Mapped[list[str]]=mapped_column(JSON,default=list);acknowledged_by:Mapped[str|None]=mapped_column(String(160))
class AlertIn(BaseModel):alert_type:str=Field(min_length=3,max_length=80);severity:str=Field(pattern='^(low|medium|high|critical)$');resource_ref:str=Field(min_length=2,max_length=240);privacy_safe_context:dict=Field(default_factory=dict)
class Triage(BaseModel):status:str=Field(pattern='^(acknowledged|contained|false_positive|resolved)$');runbook:str=Field(min_length=3,max_length=160);containment_actions:list[str]=Field(default_factory=list,max_length=30)
def analyst(c):
 if not c.roles.intersection({'security_analyst','platform_super_admin'}):raise HTTPException(403,'Security analyst role required')
@router.post('/alerts',status_code=201)
async def alert(body:AlertIn,c:ContextDep,db:AsyncSession=Depends(session)):
 analyst(c);await set_tenant(db,c.tenant_id)
 forbidden={'narrative','email','name','phone','identity'}
 if forbidden.intersection(k.lower() for k in body.privacy_safe_context):raise HTTPException(422,'Alert context contains prohibited personal-data field')
 row=Alert(tenant_id=c.tenant_id,status='open',detected_at=datetime.now(UTC),**body.model_dump());db.add(row);await db.flush();db.add(OutboxEvent(tenant_id=c.tenant_id,event_type='security.alert_opened.v1',subject=row.resource_ref,payload={'alert_id':str(row.id),'alert_type':row.alert_type,'severity':row.severity}));await db.commit();await db.refresh(row);return row
@router.post('/alerts/{alert_id}/triage')
async def triage(alert_id:UUID,body:Triage,c:ContextDep,db:AsyncSession=Depends(session)):
 analyst(c);await set_tenant(db,c.tenant_id);row=await db.get(Alert,alert_id)
 if row is None or row.tenant_id!=c.tenant_id:raise HTTPException(404,'Not found')
 if row.status in {'resolved','false_positive'}:raise HTTPException(409,'Alert is closed')
 if row.severity in {'high','critical'} and body.status=='resolved' and not body.containment_actions:raise HTTPException(422,'High-severity resolution requires containment evidence')
 row.status=body.status;row.runbook=body.runbook;row.containment_actions=body.containment_actions;row.acknowledged_by=c.subject_id;await db.commit();return row
@router.get('/alerts')
async def alerts(c:ContextDep,db:AsyncSession=Depends(session),status:str|None=None):
 analyst(c);await set_tenant(db,c.tenant_id);q=select(Alert).where(Alert.tenant_id==c.tenant_id);q=q.where(Alert.status==status) if status else q;return list(await db.scalars(q.order_by(Alert.detected_at.desc())))
app=create_app('Security Monitor Service','Privacy-safe alert ingestion, triage, containment and incident events.',[router])
