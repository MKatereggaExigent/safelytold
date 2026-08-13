from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from .config import settings
from .db import Base, engine
from .logging import configure
from .rls import apply_tenant_rls


def create_app(title:str,description:str,routers:list[APIRouter],on_ready:Callable[[],Awaitable[None]]|None=None):
 cfg=settings();configure(cfg.log_level)
 @asynccontextmanager
 async def life(_)->AsyncIterator[None]:
  if cfg.environment=="development":
   async with engine().begin() as c:await c.run_sync(Base.metadata.create_all)
  async with engine().begin() as c:await apply_tenant_rls(c)
  if on_ready:await on_ready()
  yield
 app=FastAPI(title=title,description=description,version="0.1.0",lifespan=life,docs_url="/docs" if cfg.environment!="production" else None,redoc_url=None)
 @app.get("/health")
 async def health():return {"status":"ok","service":cfg.service_name,"version":"0.1.0"}
 @app.get("/ready")
 async def ready():return {"ready":True}
 for r in routers:app.include_router(r)
 return app
