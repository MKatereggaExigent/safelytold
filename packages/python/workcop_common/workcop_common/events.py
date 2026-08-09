from datetime import UTC,datetime
from typing import Any
from uuid import UUID,uuid4
from pydantic import BaseModel,Field,field_validator
from .privacy import assert_event_safe
class CloudEvent(BaseModel):
 specversion:str="1.0";id:UUID=Field(default_factory=uuid4);source:str;type:str;subject:str
 time:datetime=Field(default_factory=lambda:datetime.now(UTC));datacontenttype:str="application/json"
 tenant_id:UUID;correlation_id:UUID=Field(default_factory=uuid4);data:dict[str,Any]
 @field_validator("data")
 @classmethod
 def safe(cls,v):assert_event_safe(v);return v
