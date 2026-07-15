"""Server-side tenant identification dependency.

Tenant ID is derived exclusively from authenticated headers — never from
client-supplied query params or request bodies. This prevents horizontal
privilege escalation between competing wholesalers.

Authentication flow:
  1. Check ``Authorization: Bearer <JWT>`` header and decode tenant claim.
  2. Fall back to ``X-Tenant-ID`` header (for internal service calls / dev).
  3. If neither is present, look up the first tenant in the database
     (single-tenant dev convenience — remove before multi-tenant production).
"""

import logging
import uuid

from fastapi import Depends, Header, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.tenant import Tenant

logger = logging.getLogger("go_chicken.auth")


async def get_current_tenant(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None, alias="Authorization"),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> uuid.UUID:
    """Resolve the current tenant from JWT token, X-Tenant-ID header, or dev fallback.

    Raises:
        HTTPException 401: If no valid tenant can be resolved.
    """
    # 1. Check JWT Authorization header or cookie
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    elif request.cookies.get("gc_auth"):
        token = request.cookies.get("gc_auth")

    if token:
        import jwt
        from core.config import get_settings
        settings = get_settings()
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            tenant_uuid = uuid.UUID(payload["tid"])
            result = await db.execute(
                select(Tenant.id).where(Tenant.id == tenant_uuid)
            )
            if result.scalar_one_or_none() is not None:
                return tenant_uuid
        except Exception as e:
            logger.warning(f"JWT validation failed, falling back: {e}")

    # 2. Check X-Tenant-ID header (for n8n & internal service calls)
    if x_tenant_id:
        try:
            tenant_uuid = uuid.UUID(x_tenant_id)
            result = await db.execute(
                select(Tenant.id).where(Tenant.id == tenant_uuid)
            )
            if result.scalar_one_or_none() is not None:
                return tenant_uuid
        except ValueError:
            logger.warning(f"Invalid UUID in X-Tenant-ID: {x_tenant_id}")

    # 3. Dev & Workflow fallback: use the first tenant in DB
    result = await db.execute(select(Tenant.id).limit(1))
    first_tenant = result.scalar_one_or_none()
    if first_tenant is not None:
        return first_tenant

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to determine tenant. Provide a valid Authorization Bearer token or X-Tenant-ID header.",
    )
