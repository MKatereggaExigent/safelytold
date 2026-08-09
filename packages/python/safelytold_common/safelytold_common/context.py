from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID
@dataclass(frozen=True,slots=True)
class RequestContext:
 tenant_id:UUID; subject_id:str; roles:frozenset[str]; purpose:str; case_ids:frozenset[UUID]=frozenset()
request_context:ContextVar[RequestContext|None]=ContextVar("request_context",default=None)
