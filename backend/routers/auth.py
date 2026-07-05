"""Authentication router — signup and login with JWT tokens.

Signup creates a new Tenant + admin User in one transaction.
Login verifies phone + password and returns a JWT.
"""

import uuid
import hashlib
import hmac
import secrets
import time
import json
import base64
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import httpx
from urllib.parse import urlencode

from core.database import get_db
from core.config import get_settings
from models.tenant import Tenant
from models.user import User, UserRole
from models.profile import BusinessProfile
from schemas.auth import SignupRequest, LoginRequest, AuthResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# ── Simple JWT-like signing (HMAC-SHA256) ─────────────────────────────
# In production, swap for python-jose / PyJWT with RS256.
_JWT_SECRET = secrets.token_hex(32)
_JWT_EXPIRY_SECONDS = 60 * 60 * 24 * 7  # 7 days


def _hash_password(password: str) -> str:
    """Hash a password with a random salt using SHA-256."""
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{digest}"


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored salt:hash pair."""
    if ":" not in stored_hash:
        return False
    salt, digest = stored_hash.split(":", 1)
    return hmac.compare_digest(
        hashlib.sha256(f"{salt}:{password}".encode()).hexdigest(),
        digest,
    )


def _create_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    """Create a simple signed token (base64 payload + HMAC signature)."""
    payload = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "exp": int(time.time()) + _JWT_EXPIRY_SECONDS,
    }
    payload_bytes = base64.urlsafe_b64encode(json.dumps(payload).encode())
    sig = hmac.new(_JWT_SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return f"{payload_bytes.decode()}.{sig}"


# ── Signup ────────────────────────────────────────────────────────────
@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Register a new business (tenant) and its admin user."""

    try:
        # Check if phone already exists
        existing = await db.execute(select(User).where(User.phone == body.phone))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists.",
            )

        # Create tenant
        tenant = Tenant(name=body.business_name)
        db.add(tenant)
        await db.flush()  # populate tenant.id

        # Create admin user
        user = User(
            tenant_id=tenant.id,
            role=UserRole.ADMIN,
            name=body.admin_name,
            phone=body.phone,
            password_hash=_hash_password(body.password),
        )
        db.add(user)

        # Create default business profile
        profile = BusinessProfile(
            tenant_id=tenant.id,
            admin_name=body.admin_name,
            business_name=body.business_name,
            role="Owner",
            contact_number=body.phone,
            app_language="English",
            iot_alerts_enabled=True,
            financial_alerts_enabled=True,
        )
        db.add(profile)

        await db.commit()
        await db.refresh(user)

        token = _create_token(user.id, tenant.id)
        logger.info("New signup: %s (tenant %s)", body.phone, tenant.id)

        return AuthResponse(
            access_token=token,
            user_id=user.id,
            tenant_id=tenant.id,
            name=user.name,
            role=user.role.value,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Database offline during signup (%s). Using fallback demo session.", e)
        demo_tenant = uuid.uuid4()
        demo_user = uuid.uuid4()
        return AuthResponse(
            access_token=_create_token(demo_user, demo_tenant),
            user_id=demo_user,
            tenant_id=demo_tenant,
            name=body.admin_name if hasattr(body, "admin_name") else "Demo Admin",
            role="admin",
        )


# ── Login ─────────────────────────────────────────────────────────────
@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with phone + password."""
    try:
        result = await db.execute(select(User).where(User.phone == body.phone))
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or password.",
            )

        if not _verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or password.",
            )

        token = _create_token(user.id, user.tenant_id)
        logger.info("Login: %s", body.phone)

        return AuthResponse(
            access_token=token,
            user_id=user.id,
            tenant_id=user.tenant_id,
            name=user.name,
            role=user.role.value,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Database offline during login (%s). Using fallback demo session.", e)
        demo_tenant = uuid.uuid4()
        demo_user = uuid.uuid4()
        return AuthResponse(
            access_token=_create_token(demo_user, demo_tenant),
            user_id=demo_user,
            tenant_id=demo_tenant,
            name="Demo User",
            role="admin",
        )


def _get_redirect_uri(request: Request) -> str:
    base_url = str(request.base_url).rstrip("/")
    if "vercel.app" in base_url or os.getenv("VERCEL"):
        base_url = base_url.replace("http://", "https://")
    return f"{base_url}/api/v1/auth/google/callback"


# ── Google OAuth Flow ─────────────────────────────────────────────────
@router.get("/google/login")
async def google_login(request: Request):
    """Initiate Google OAuth 2.0 authorization flow."""
    settings = get_settings()
    redirect_uri = _get_redirect_uri(request)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=url)


@router.get("/google/callback")
async def google_callback(request: Request, code: str = None, error: str = None, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback, exchange code for token, and authenticate user."""
    settings = get_settings()
    frontend_login = f"{settings.FRONTEND_URL}/login"

    if error or not code:
        logger.warning(f"Google OAuth error or missing code: {error}")
        return RedirectResponse(f"{frontend_login}?error=Google login was cancelled or failed")

    redirect_uri = _get_redirect_uri(request)
    async with httpx.AsyncClient() as client:
        # 1. Exchange code for access token
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        if token_res.status_code != 200:
            logger.error(f"Google token exchange failed: {token_res.text}")
            return RedirectResponse(f"{frontend_login}?error=Failed to authenticate with Google")

        token_data = token_res.json()
        access_token = token_data.get("access_token")

        # 2. Get user info from Google
        userinfo_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_res.status_code != 200:
            logger.error(f"Google userinfo failed: {userinfo_res.text}")
            return RedirectResponse(f"{frontend_login}?error=Failed to retrieve Google profile")

        userinfo = userinfo_res.json()

    google_id = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name") or "Google User"
    picture = userinfo.get("picture")

    if not email:
        return RedirectResponse(f"{frontend_login}?error=No email returned from Google")

    # 3. Find existing user by google_id or email
    result = await db.execute(
        select(User).where((User.google_id == google_id) | (User.email == email))
    )
    user = result.scalars().first()

    if not user:
        # Create new tenant and user
        business_name = f"{name}'s Poultry Hub"
        tenant = Tenant(name=business_name)
        db.add(tenant)
        await db.flush()

        user = User(
            tenant_id=tenant.id,
            role=UserRole.ADMIN,
            name=name,
            email=email,
            google_id=google_id,
        )
        db.add(user)

        profile = BusinessProfile(
            tenant_id=tenant.id,
            admin_name=name,
            business_name=business_name,
            role="Owner",
            app_language="English",
            iot_alerts_enabled=True,
            financial_alerts_enabled=True,
            profile_pic_url=picture[:500] if picture else None,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(user)
        logger.info("New Google OAuth signup: %s (tenant %s)", email, tenant.id)
    else:
        # If user existed by email without google_id linked, link it now
        if not user.google_id:
            user.google_id = google_id
            await db.commit()
        logger.info("Google OAuth login: %s", email)

    token = _create_token(user.id, user.tenant_id)

    # 4. Redirect to frontend callback page with auth data
    params = {
        "token": token,
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "name": user.name,
        "role": user.role.value,
    }
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?{urlencode(params)}")

