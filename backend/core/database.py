from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from core.config import get_settings

DATABASE_URL = os.getenv("DATABASE_URL", get_settings().DATABASE_URL)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
from models.base import Base

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
