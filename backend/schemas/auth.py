"""Pydantic schemas for authentication (signup / login)."""

from pydantic import BaseModel, ConfigDict, Field, field_validator
import uuid
import re


class SignupRequest(BaseModel):
    """Fields required to create a new admin user + tenant."""

    business_name: str = Field(..., min_length=2, max_length=255)
    admin_name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{6,14}$")
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must contain both letters and numbers")
        return v


class LoginRequest(BaseModel):
    """Phone + password login."""

    phone: str = Field(..., pattern=r"^\+?[1-9]\d{6,14}$")
    password: str = Field(..., min_length=1, max_length=128)


class OAuthRequest(BaseModel):
    """OAuth login via Supabase."""

    access_token: str
    provider_token: str


class AuthResponse(BaseModel):
    """Returned on successful signup or login."""

    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)
