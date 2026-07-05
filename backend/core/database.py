from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Change this in backend/core/database.py
DATABASE_URL = "postgresql+asyncpg://postgres:adminpassword@localhost:5435/go_chicken"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
from models.base import Base

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
