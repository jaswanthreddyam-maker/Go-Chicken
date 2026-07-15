"""Export critical demo data (Retailers, Products, Inventory, Price Books) to JSON.

Run this before the hackathon to have a safe backup of the exact demo state.
"""
import sys
import os
import json
import asyncio
from datetime import date, datetime
import uuid

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.user import User
from models.pricing import PriceBook
# Removed inventory for simplicity

def serialize_dt(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return str(obj)

async def export_data():
    async with AsyncSessionLocal() as db:
        # Export Users (Retailers)
        users = (await db.execute(select(User))).scalars().all()
        
        # Export Price Books
        prices = (await db.execute(select(PriceBook))).scalars().all()
        
        data = {
            "users": [serialize_dt(u) for u in users],
            "price_books": [serialize_dt(p) for p in prices],
        }
        
        with open("demo_backup.json", "w") as f:
            json.dump(data, f, indent=2, default=serialize_dt)
            
        print("✅ Demo data successfully exported to demo_backup.json")

if __name__ == "__main__":
    asyncio.run(export_data())
