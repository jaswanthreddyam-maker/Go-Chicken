import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict
from decimal import Decimal

class ProfileBase(BaseModel):
    admin_name: Optional[str] = None
    role: Optional[str] = None
    business_name: Optional[str] = None
    gstin: Optional[str] = None
    contact_number: Optional[str] = None
    hub_location: Optional[str] = None
    base_price_today: Optional[Decimal] = None
    default_credit_limit: Optional[Decimal] = None
    iot_alerts_enabled: Optional[bool] = None
    financial_alerts_enabled: Optional[bool] = None
    app_language: Optional[str] = None
    profile_pic_url: Optional[str] = None

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class ProfileResponse(ProfileBase):
    id: uuid.UUID
    tenant_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
