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
import jwt
import bcrypt

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import httpx
from urllib.parse import urlencode
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.database import get_db
from core.config import get_settings
from models.tenant import Tenant
from models.user import User, UserRole
from models.profile import BusinessProfile
from schemas.auth import SignupRequest, LoginRequest, AuthResponse, OAuthRequest
from supabase import create_client, Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)

# In production, swap for python-jose / PyJWT with RS256.


def _mask_pii(value: str) -> str:
    if not value: return "***"
    if "@" in value:
        user, domain = value.split("@", 1)
        return f"{user[:2]}***@{domain}" if len(user) > 2 else f"***@{domain}"
    if len(value) > 4:
        return value[:3] + "***" + value[-2:]
    return "***"

def _hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored bcrypt hash or legacy SHA256 hash."""
    try:
        # Legacy SHA256 format
        if ":" in stored_hash:
            salt, digest = stored_hash.split(":", 1)
            return hmac.compare_digest(
                hashlib.sha256(f"{salt}:{password}".encode()).hexdigest(),
                digest,
            )
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    except Exception:
        return False


def _create_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    """Create a signed JWT token using PyJWT."""
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "exp": int(time.time()) + (60 * 60 * 24 * 7),  # 7 days
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


# ── Signup ────────────────────────────────────────────────────────────
@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def signup(request: Request, body: SignupRequest, response: Response, db: AsyncSession = Depends(get_db)):
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
        logger.info("New signup: %s (tenant %s)", _mask_pii(body.phone), tenant.id)
        
        response.set_cookie(
            "gc_auth", token,
            max_age=60*60*24*7, httponly=True, secure=True, samesite="lax"
        )

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
        logger.error("Database error during signup: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )


# ── Login ─────────────────────────────────────────────────────────────
@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
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
        logger.info("Login: %s", _mask_pii(body.phone))

        response.set_cookie(
            "gc_auth", token,
            max_age=60*60*24*7, httponly=True, secure=True, samesite="lax"
        )

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
        logger.error("Database error during login: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )

# ── OAuth ─────────────────────────────────────────────────────────────
@router.post("/oauth/google", response_model=AuthResponse)
@limiter.limit("10/minute")
async def oauth_google(request: Request, body: OAuthRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """Authenticate with Supabase Google OAuth access token."""
    settings = get_settings()
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(status_code=500, detail="Supabase not configured")
        
    try:
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        # Verify the token by fetching the user profile from Supabase
        user_resp = supabase.auth.get_user(body.access_token)
        sb_user = user_resp.user
        
        if not sb_user:
            raise HTTPException(status_code=401, detail="Invalid OAuth token")
            
        email = sb_user.email
        provider_user_id = sb_user.id
        
        # Identity meta
        user_meta = sb_user.user_metadata or {}
        full_name = user_meta.get("full_name", "Google User")
        avatar_url = user_meta.get("avatar_url", None)
        
        # Find user by email or provider_user_id
        result = await db.execute(
            select(User).where((User.email == email) | (User.provider_user_id == provider_user_id))
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Link account if not already linked
            if not user.provider_user_id:
                user.auth_provider = "google"
                user.provider_user_id = provider_user_id
                user.avatar_url = avatar_url
                await db.commit()
            
            tenant_id = user.tenant_id
        else:
            # Automatic Tenant Creation
            tenant = Tenant(name=f"{full_name}'s Business")
            db.add(tenant)
            await db.flush()
            
            tenant_id = tenant.id
            
            # Create User
            user = User(
                tenant_id=tenant_id,
                email=email,
                name=full_name,
                auth_provider="google",
                provider_user_id=provider_user_id,
                avatar_url=avatar_url,
                role=UserRole.ADMIN,
            )
            db.add(user)
            await db.commit()
            
            # Seed inventory and pricing for the new tenant
            from core.inventory_service import InventoryService
            from core.pricing_service import get_all_prices
            await InventoryService.get_all_inventory(db, tenant_id)
            await get_all_prices(db)
            
            # Create Profile
            profile = BusinessProfile(
                tenant_id=tenant.id,
                admin_name=full_name,
                business_name=f"{full_name}'s Business",
                role="Owner",
                app_language="English",
                iot_alerts_enabled=True,
                financial_alerts_enabled=True,
            )
            db.add(profile)
            
            await db.commit()
            await db.refresh(user)
            
        # Issue local token
        token = _create_token(user.id, tenant_id)
        
        response.set_cookie(
            "gc_auth", token,
            max_age=60*60*24*7, httponly=True, secure=True, samesite="lax"
        )

        return AuthResponse(
            access_token=token,
            user_id=user.id,
            tenant_id=tenant_id,
            name=user.name,
            role=user.role.value,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("OAuth error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify OAuth token.",
        )


@router.post("/logout")
async def logout(response: Response):
    """Clear the HTTP-only auth cookie."""
    response.delete_cookie("gc_auth", httponly=True, secure=True, samesite="lax")
    return {"message": "Successfully logged out"}


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
    state = secrets.token_urlsafe(32)
    redirect_uri = _get_redirect_uri(request)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state,
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    response = RedirectResponse(url=url)
    response.set_cookie(
        "oauth_state", state,
        max_age=600, httponly=True, secure=True, samesite="lax"
    )
    return response


@router.get("/google/callback")
async def google_callback(request: Request, code: str = None, error: str = None, state: str = None, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback, exchange code for token, and authenticate user."""
    settings = get_settings()
    frontend_login = f"{settings.FRONTEND_URL}/login"

    cookie_state = request.cookies.get("oauth_state")
    if not state or state != cookie_state:
        logger.warning("Invalid OAuth state. Potential CSRF.")
        return RedirectResponse(f"{frontend_login}?error=Invalid OAuth state")

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
        logger.info("New Google OAuth signup: %s (tenant %s)", _mask_pii(email), tenant.id)
    else:
        # If user existed by email without google_id linked, link it now
        if not user.google_id:
            user.google_id = google_id
            await db.commit()
        logger.info("Google OAuth login: %s", _mask_pii(email))

    token = _create_token(user.id, user.tenant_id)

    # 4. Redirect to frontend callback page with auth data
    params = {
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "name": user.name,
        "role": user.role.value,
    }
    response = RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?{urlencode(params)}")
    response.set_cookie(
        "gc_auth", token,
        max_age=60*60*24*7, httponly=True, secure=True, samesite="lax"
    )
    return response

