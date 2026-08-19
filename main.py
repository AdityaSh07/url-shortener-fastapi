from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.database.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(
    title="URL Shortener API",
    description="A simple URL shortener built with FastAPI and PostgreSQL",
    lifespan=lifespan,
)

app.include_router(router)