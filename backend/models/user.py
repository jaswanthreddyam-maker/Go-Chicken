import uuid
import enum
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Enum, Sequence
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DRIVER = "driver"
    RETAILER = "retailer"


class User(Base):
    """Represents an admin, driver, or retailer within a tenant."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    whatsapp_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    
    # OAuth Identity Fields
    auth_provider: Mapped[str | None] = mapped_column(String(50), default="local")
    provider_user_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    password_hash: Mapped[str | None] = mapped_column(String(255))

    # Retailer routing fields
    shop_address: Mapped[str | None] = mapped_column(Text)
    shop_name: Mapped[str | None] = mapped_column(String(255))
    
    # We define a Sequence here for PostgreSQL atomic IDs. 
    # retailer_id is mapped as string, we will assign it manually in Python with f"GC-RET-{nextval:06d}"
    retailer_id: Mapped[str | None] = mapped_column(String(50), unique=True)
    zone: Mapped[str | None] = mapped_column(String(100))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(11, 8))

    # Preferences
    preferred_language: Mapped[str | None] = mapped_column(String(10), default=None)
    
    # Status
    onboarding_status: Mapped[str] = mapped_column(String(50), server_default="ACTIVE", default="ACTIVE")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    orders = relationship("Order", back_populates="retailer")
    khata_transactions = relationship("KhataTransaction", back_populates="retailer")
    truck = relationship("Truck", back_populates="driver", uselist=False)
