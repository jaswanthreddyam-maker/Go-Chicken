"""Pydantic schemas for authentication (signup / login)."""

from pydantic import BaseModel, ConfigDict
import uuid


class SignupRequest(BaseModel):
    """Fields required to create a new admin user + tenant."""

    business_name: str
    admin_name: str
    phone: str
    password: str


class LoginRequest(BaseModel):
    """Phone + password login."""

    phone: str
    password: str


class AuthResponse(BaseModel):
    """Returned on successful signup or login."""

    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)
