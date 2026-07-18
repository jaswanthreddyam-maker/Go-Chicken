import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from decimal import Decimal
import re

class ProfileBase(BaseModel):
    admin_name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, max_length=100)
    business_name: Optional[str] = Field(None, max_length=255)
    gstin: Optional[str] = Field(None, max_length=15)
    contact_number: Optional[str] = Field(None, max_length=20)
    hub_location: Optional[str] = Field(None, max_length=255)
    base_price_today: Optional[Decimal] = Field(None, ge=0)
    default_credit_limit: Optional[Decimal] = Field(None, ge=0)
    iot_alerts_enabled: Optional[bool] = None
    financial_alerts_enabled: Optional[bool] = None
    app_language: Optional[str] = Field(None, max_length=50)
    profile_pic_url: Optional[str] = Field(None, max_length=500)

    @field_validator('contact_number')
    @classmethod
    def validate_contact_number(cls, v):
        if v is not None:
            # Strip non-digits and leading +
            clean = re.sub(r'[^0-9+]', '', v)
            if not clean:
                return v
            if not re.match(r'^\+?[1-9]\d{9,14}$', clean):
                raise ValueError('Invalid phone number format')
        return v

    @field_validator('gstin')
    @classmethod
    def validate_gstin(cls, v):
        if v is not None:
            if v.strip() == '':
                return v
            # Basic Indian GSTIN format: 2 digits, 10 PAN, 1 entity, 1 Z, 1 checksum
            if not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', v.upper()):
                raise ValueError('Invalid GSTIN format')
            return v.upper()
        return v

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class ProfileResponse(ProfileBase):
    id: uuid.UUID
    tenant_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
