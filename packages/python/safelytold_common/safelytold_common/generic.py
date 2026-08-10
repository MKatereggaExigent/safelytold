from typing import Any
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field,ConfigDict
from sqlalchemy import JSON,String,func,select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped,mapped_column
from .auth import ContextDep,OptionalContextDep
from .config import settings
from .db import Base,TenantMixin,OutboxEvent,session,set_tenant
class Record(TenantMixin,Base):
 __tablename__="domain_records";kind:Mapped[str]=mapped_column(String(80),index=True);payload:Mapped[dict[str,Any]]=mapped_column(JSON,default=dict)
class Create(BaseModel):kind:str=Field(min_length=1,max_length=80);payload:dict[str,Any]=Field(default_factory=dict)
class View(BaseModel):
 model_config=ConfigDict(from_attributes=True);id:UUID;tenant_id:UUID;kind:str;status:str;payload:dict[str,Any]
def router(slug:str,event_type:str|None=None,public_kinds:frozenset[str]=frozenset()):
 r=APIRouter(prefix="/v1/records",tags=[slug])
 @r.post("",response_model=View)
 async def create(b:Create,c:OptionalContextDep,s:AsyncSession=Depends(session)):
  if c is None:
   if b.kind not in public_kinds:raise HTTPException(401,"Authentication required")
   tenant_id=UUID(settings().public_tenant_id)
  else:tenant_id=c.tenant_id
  await set_tenant(s,tenant_id);x=Record(tenant_id=tenant_id,kind=b.kind,payload=b.payload);s.add(x);await s.flush()
  if event_type:s.add(OutboxEvent(tenant_id=tenant_id,event_type=event_type,subject=f"{slug}/{x.id}",payload={"record_id":str(x.id),"kind":b.kind,"status":x.status}))
  await s.commit();await s.refresh(x);return x
 @r.get("/count")
 async def counting(
  c:ContextDep,s:AsyncSession=Depends(session),
  kind:str|None=None,status:str|None=None,case_id:UUID|None=None,
 ):
  await set_tenant(s,c.tenant_id)
  q=select(func.count()).select_from(Record).where(Record.tenant_id==c.tenant_id)
  if kind:q=q.where(Record.kind==kind)
  if status:q=q.where(Record.payload["status"].as_string()==status)
  if case_id:q=q.where(Record.payload["case_id"].as_string()==str(case_id))
  return {"total":(await s.scalar(q)) or 0}
 @r.get("",response_model=list[View])
 async def listing(
  c:ContextDep,s:AsyncSession=Depends(session),
  kind:str|None=None,status:str|None=None,case_id:UUID|None=None,
  limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),
 ):
  await set_tenant(s,c.tenant_id)
  q=select(Record).where(Record.tenant_id==c.tenant_id)
  if kind:q=q.where(Record.kind==kind)
  if status:q=q.where(Record.payload["status"].as_string()==status)
  if case_id:q=q.where(Record.payload["case_id"].as_string()==str(case_id))
  q=q.order_by(Record.created_at.desc(),Record.id.desc()).limit(limit).offset(offset)
  return list(await s.scalars(q))
 @r.get("/{record_id}",response_model=View)
 async def get(record_id:UUID,c:ContextDep,s:AsyncSession=Depends(session)):
  await set_tenant(s,c.tenant_id);x=await s.get(Record,record_id)
  if x is None or x.tenant_id!=c.tenant_id:raise HTTPException(404,"Not found")
  return x
 return r
