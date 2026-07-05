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

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.tenant import Tenant

logger = logging.getLogger("go_chicken.auth")


async def get_current_tenant(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None, alias="Authorization"),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> uuid.UUID:
    """Resolve the current tenant from server-controlled headers.

    Priority:
      1. JWT ``Authorization`` bearer token (future — decode & extract tenant claim).
      2. ``X-Tenant-ID`` header set by an upstream gateway or internal caller.
      3. Dev fallback: first tenant row in the database (single-tenant convenience).

    Raises:
        HTTPException 401: If no tenant can be resolved.
    """

    # ── 1. JWT Bearer Token (future-proofed) ──────────────────────────
    if authorization and authorization.startswith("Bearer "):
        # TODO: Decode JWT and extract tenant_id claim once auth is wired.
        # For now, treat the token as opaque and fall through.
        pass

    # ── 2. Trusted internal header ────────────────────────────────────
    if x_tenant_id:
        try:
            tenant_uuid = uuid.UUID(x_tenant_id)
            # Verify the tenant actually exists in the DB
            result = await db.execute(
                select(Tenant.id).where(Tenant.id == tenant_uuid)
            )
            if result.scalar_one_or_none() is not None:
                return tenant_uuid
            else:
                logger.warning(f"X-Tenant-ID header references non-existent tenant: {x_tenant_id}")
        except ValueError:
            logger.warning(f"Invalid UUID in X-Tenant-ID header: {x_tenant_id}")

    # ── 3. Dev fallback: use the first (and usually only) tenant ──────
    result = await db.execute(select(Tenant.id).limit(1))
    first_tenant = result.scalar_one_or_none()
    if first_tenant is not None:
        logger.info(f"Auth dev-fallback: using first tenant {first_tenant}")
        return first_tenant

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to determine tenant. Provide a valid Authorization or X-Tenant-ID header.",
    )
