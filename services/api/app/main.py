"""FastAPI application factory."""

from fastapi import FastAPI

from .config import get_settings
from .models import Base
from .db import engine
from .routers import health, public_intake


settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.include_router(health.router)
    app.include_router(public_intake.router)

    @app.on_event("startup")
    async def _startup() -> None:  # noqa: D401
        """Run startup tasks such as ensuring metadata is created in dev."""
        if settings.environment == "development":
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

    return app


app = create_app()
