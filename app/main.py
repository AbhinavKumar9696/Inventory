import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.init_db import seed_default_admin
from app.db.session import AsyncSessionLocal, redis_client
from app.repositories.user_repository import UserRepository

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await redis_client.ping()
    logger.info("Redis connected.")

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        await seed_default_admin(user_repo)

    yield

    await redis_client.aclose()


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)

