from sqlalchemy import Column, String, Numeric, DateTime, func
from models.base import Base

class ProductPrice(Base):
    """Database model for dynamic pricing of poultry items."""
    __tablename__ = "product_prices"

    item_type = Column(String(50), primary_key=True)  # "Live Bird", "Dressed", "Skinless"
    price_per_kg = Column(Numeric(10, 2), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
