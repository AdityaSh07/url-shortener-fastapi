from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
    )
from sqlalchemy.ext.declarative import declarative_base
from ..core.config import settings 


engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
)

Base = declarative_base()

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # after committing sqlalchemy object will still contain object details
    autoflush=False,
    autocommit=False
)

async def get_db():
    async with SessionLocal() as db:
        yield db