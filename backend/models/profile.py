import uuid
from decimal import Decimal
from sqlalchemy import String, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    admin_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str | None] = mapped_column(String(100))
    business_name: Mapped[str | None] = mapped_column(String(255))
    gstin: Mapped[str | None] = mapped_column(String(50))
    contact_number: Mapped[str | None] = mapped_column(String(20))
    hub_location: Mapped[str | None] = mapped_column(String(255))
    
    base_price_today: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    default_credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    
    iot_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    financial_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    app_language: Mapped[str] = mapped_column(String(50), default="English")
    profile_pic_url: Mapped[str | None] = mapped_column(String(500))
    
    tenant = relationship("Tenant", backref="business_profile")
