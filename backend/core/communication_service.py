"""PR 8 Core Multi-Channel Communication Service & Lifecycle Engine."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.communication import CommunicationLog
from core.communication_templates import TemplateRegistry, default_template_registry, TemplateRenderingError
from core.communication_providers import ProviderRegistry, UnsupportedChannelError, ProviderDeliveryResult

logger = logging.getLogger("gochicken.communication_service")


class CommunicationService:
    """Enterprise multi-channel communication engine with strict audit logging, template rendering, and provider routing."""

    def __init__(
        self,
        provider_registry: ProviderRegistry,
        template_registry: TemplateRegistry = default_template_registry,
        max_retries: int = 3,
    ) -> None:
        self.provider_registry = provider_registry
        self.template_registry = template_registry
        self.max_retries = max_retries

    async def get_log_by_idempotency_key(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        idempotency_key: str,
    ) -> Optional[CommunicationLog]:
        """Look up existing communication log entry by tenant and idempotency key."""
        stmt = select(CommunicationLog).where(
            CommunicationLog.tenant_id == tenant_id,
            CommunicationLog.idempotency_key == idempotency_key,
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def send(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        recipient: str,
        template_id: str,
        context: Dict[str, Any],
        idempotency_key: str,
        channel: str = "WHATSAPP",
        fallback_channels: Optional[List[str]] = None,
        commit: bool = False,
    ) -> CommunicationLog:
        """Render template and dispatch customer message via provider with idempotency and retry/fallback support."""
        # 1. Idempotency Check
        existing = await self.get_log_by_idempotency_key(db, tenant_id, idempotency_key)
        if existing:
            logger.info(
                f"[COMMUNICATION IDEMPOTENT] Duplicate message dispatch request {idempotency_key} ignored. Returning existing log."
            )
            return existing

        # 2. Primary Provider Resolution (raises UnsupportedChannelError on unregistered channel)
        provider = self.provider_registry.resolve(channel)

        # 3. Template Resolution & Rendering (raises TemplateRenderingError on missing vars)
        template = self.template_registry.resolve(template_id, channel)
        rendered_content = template.render(context)

        now = datetime.now(timezone.utc)
        log_entry = CommunicationLog(
            tenant_id=tenant_id,
            recipient=recipient,
            channel=channel.upper(),
            template_id=template_id.upper(),
            rendered_content=rendered_content,
            status="PENDING",
            idempotency_key=idempotency_key,
            retry_count=0,
            created_at=now,
            updated_at=now,
        )
        db.add(log_entry)

        # 4. Dispatch attempt
        delivery_res = await provider.send(
            recipient=recipient,
            content=rendered_content,
            metadata={"template_id": template_id, "idempotency_key": idempotency_key},
        )

        if delivery_res.success:
            log_entry.status = delivery_res.status
            log_entry.provider_message_id = delivery_res.provider_message_id
            log_entry.updated_at = datetime.now(timezone.utc)
        else:
            # Check for provider fallback
            fallback_succeeded = False
            if fallback_channels:
                for fb_chan in fallback_channels:
                    try:
                        fb_template = self.template_registry.resolve(template_id, fb_chan)
                        fb_content = fb_template.render(context)
                        fb_provider = self.provider_registry.resolve(fb_chan)
                        fb_res = await fb_provider.send(recipient, fb_content, metadata={"fallback_for": channel})
                        if fb_res.success:
                            log_entry.channel = fb_chan.upper()
                            log_entry.rendered_content = fb_content
                            log_entry.status = fb_res.status
                            log_entry.provider_message_id = fb_res.provider_message_id
                            log_entry.updated_at = datetime.now(timezone.utc)
                            fallback_succeeded = True
                            break
                    except Exception as e:
                        logger.warning(f"[COMMUNICATION FALLBACK FAILED] Channel {fb_chan} failed: {e}")

            if not fallback_succeeded:
                log_entry.retry_count += 1
                log_entry.error_message = delivery_res.error_message
                if log_entry.retry_count >= self.max_retries:
                    log_entry.status = "FAILED_PERMANENT"
                else:
                    log_entry.status = "RETRYING"
                log_entry.updated_at = datetime.now(timezone.utc)

        if commit:
            await db.commit()
            await db.refresh(log_entry)

        return log_entry

    async def update_delivery_status(
        self,
        db: AsyncSession,
        log_id: UUID,
        new_status: str,
        commit: bool = True,
    ) -> Optional[CommunicationLog]:
        """Update lifecycle status from provider webhook (e.g., DELIVERED -> READ)."""
        stmt = select(CommunicationLog).where(CommunicationLog.id == log_id)
        result = await db.execute(stmt)
        log_entry = result.scalars().first()
        if not log_entry:
            return None

        log_entry.status = new_status.upper()
        log_entry.updated_at = datetime.now(timezone.utc)
        if commit:
            await db.commit()
            await db.refresh(log_entry)
        return log_entry
