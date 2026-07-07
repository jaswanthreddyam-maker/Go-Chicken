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
) -> uuid.UUID:
    """Resolve the current tenant from the JWT Authorization header or cookie.

    Raises:
        HTTPException 401: If no valid token is provided.
    """

    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    elif request.cookies.get("gc_auth"):
        token = request.cookies.get("gc_auth")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to determine tenant. Provide a valid Authorization Bearer token or gc_auth cookie.",
        )
    
    # Import jwt here to avoid circular imports if any, or at the top of file
    import jwt
    from core.config import get_settings
    
    settings = get_settings()
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        tenant_uuid = uuid.UUID(payload["tid"])
        
        # Verify the tenant actually exists in the DB
        result = await db.execute(
            select(Tenant.id).where(Tenant.id == tenant_uuid)
        )
        if result.scalar_one_or_none() is not None:
            return tenant_uuid
        else:
            logger.warning(f"JWT token references non-existent tenant: {tenant_uuid}")
            raise HTTPException(status_code=401, detail="Invalid tenant")
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except (jwt.InvalidTokenError, KeyError, ValueError) as e:
        logger.warning(f"Invalid JWT: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
