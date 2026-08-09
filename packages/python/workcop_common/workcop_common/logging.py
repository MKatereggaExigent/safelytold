import json,logging
from datetime import UTC,datetime
from .privacy import redact_mapping
class PrivacyFormatter(logging.Formatter):
 def format(self,r):
  p={"timestamp":datetime.now(UTC).isoformat(),"level":r.levelname,"logger":r.name,"message":r.getMessage()}
  x=getattr(r,"safe_extra",None)
  if isinstance(x,dict):p["context"]=redact_mapping(x)
  if r.exc_info:p["exception_type"]=r.exc_info[0].__name__ if r.exc_info[0] else None
  return json.dumps(p,default=str)
def configure(level="INFO"):
 h=logging.StreamHandler();h.setFormatter(PrivacyFormatter());root=logging.getLogger();root.handlers.clear();root.addHandler(h);root.setLevel(level)
