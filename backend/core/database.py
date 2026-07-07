from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from core.config import get_settings

DATABASE_URL = os.getenv("DATABASE_URL", get_settings().DATABASE_URL)

engine = create_async_engine(
    DATABASE_URL, 
    echo=get_settings().DEBUG,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
from models.base import Base

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
