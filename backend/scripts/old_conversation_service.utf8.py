"""Conversation State Machine Service for WhatsApp Order Assistant."""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.conversation_state import ConversationState
from models.user import User
from core.whatsapp_i18n import get_message

logger = logging.getLogger("go_chicken.conversation_service")

# Time after which a conversation state resets to IDLE
SESSION_TIMEOUT_MINUTES = 30


class ConversationService:
    """State machine and deterministic response generator for WhatsApp."""

    @staticmethod
    async def get_or_create_state(db: AsyncSession, user: User) -> ConversationState:
        """Fetch existing conversation state for user, or create a new one."""
        result = await db.execute(
            select(ConversationState).where(ConversationState.user_id == user.id)
        )
        state = result.scalars().first()

        if not state:
            state = ConversationState(
                user_id=user.id,
                tenant_id=user.tenant_id,
                language=user.preferred_language
            )
            db.add(state)
            await db.commit()
            await db.refresh(state)
        
        # Sync language from user to state if user already picked it
        if user.preferred_language and state.language != user.preferred_language:
            state.language = user.preferred_language
            await db.commit()

        return state

    @staticmethod
    async def reset_state(db: AsyncSession, state: ConversationState):
        """Reset conversation state to IDLE and clear context."""
        state.state = "IDLE"
        state.pending_intent = None
        state.pending_product = None
        state.pending_quantity = None
        state.pending_quote_id = None
        state.pending_price_per_kg = None
        state.pending_total = None
        state.handoff_requested = False
        state.updated_at = datetime.now(timezone.utc)
        await db.commit()

    @staticmethod
    async def reset_if_expired(db: AsyncSession, state: ConversationState) -> bool:
        """If session is older than timeout, reset to IDLE and return True."""
        now = datetime.now(timezone.utc)
        if state.updated_at < now - timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            # Only reset if we are not already IDLE
            if state.state != "IDLE":
                await ConversationService.reset_state(db, state)
                return True
        return False

    @staticmethod
    def get_main_menu_buttons() -> list[dict[str, str]]:
        """Return the standard interactive list options for Main Menu.
        Note: WhatsApp allows 3 buttons max for standard interactive messages.
        For menus, we mock this as returning top 3, or expecting list messages.
        Here we return 3 priority actions for buttons.
        """
        return [
            {"id": "menu_order", "title": "≡ƒôª Place Order"},
            {"id": "menu_prices", "title": "≡ƒÆ░ Check Prices"},
            {"id": "menu_khata", "title": "≡ƒÆ│ Khata"},
        ]

    @staticmethod
    def get_product_buttons() -> list[dict[str, str]]:
        return [
            {"id": "product_live", "title": "≡ƒÉö Live Bird"},
            {"id": "product_dressed", "title": "≡ƒìù Dressed"},
            {"id": "product_skinless", "title": "≡ƒÑ⌐ Skinless"},
        ]

    @staticmethod
    async def handle_language_selection(
        db: AsyncSession, state: ConversationState, user: User, button_id: str
    ) -> list[dict]:
        """Handle language button click and transition to Welcome."""
        lang_map = {"lang_en": "en", "lang_hi": "hi", "lang_te": "te"}
        chosen_lang = lang_map.get(button_id)
        
        if not chosen_lang:
            # Re-prompt
            return [{
                "type": "interactive",
                "text": get_message("LANGUAGE_SELECTION", "en"),
                "buttons": [
                    {"id": "lang_en", "title": "≡ƒç«≡ƒç│ English"},
                    {"id": "lang_hi", "title": "≡ƒç«≡ƒç│ αñ╣αñ┐αñ¿αÑìαñªαÑÇ"},
                    {"id": "lang_te", "title": "≡ƒç«≡ƒç│ α░ñα▒åα░▓α▒üα░ùα▒ü"}
                ]
            }]
        
        # Save preference
        user.preferred_language = chosen_lang
        state.language = chosen_lang
        state.state = "IDLE"
        await db.commit()

        # Send personalized welcome with today's Live Bird price
        from core.pricing_service import get_price_for_item
        live_bird_price = await get_price_for_item(db, "Live Bird")

        welcome_text = get_message(
            "WELCOME_WITH_RATE", 
            chosen_lang, 
            name=user.name, 
            rate=live_bird_price
        )
        menu_text = get_message("MAIN_MENU", chosen_lang)

        return [
            {"type": "text", "text": welcome_text},
            {
                "type": "interactive",
                "text": menu_text,
                "buttons": ConversationService.get_main_menu_buttons()
            }
        ]

    @staticmethod
    async def generate_order_preview(
        db: AsyncSession, state: ConversationState, user: User
    ) -> dict:
        """Generate order preview card after quantity is set."""
        from core.pricing_service import get_price_for_item
        
        rate = await get_price_for_item(db, state.pending_product)
        qty = Decimal(str(state.pending_quantity))
        total = rate * qty

        # Cache for confirmation step
        state.pending_price_per_kg = rate
        state.pending_total = total
        state.state = "AWAITING_CONFIRMATION"
        await db.commit()

        # Fetch Khata
        from models.khata import KhataTransaction
        result = await db.execute(
            select(KhataTransaction)
            .where(KhataTransaction.retailer_id == user.id)
            .order_by(KhataTransaction.created_at.desc())
            .limit(1)
        )
        last_tx = result.scalars().first()
        balance = last_tx.running_balance if last_tx else Decimal("0.00")

        preview_text = get_message(
            "ORDER_PREVIEW",
            state.language,
            product=state.pending_product,
            qty=qty,
            rate=rate,
            total=total,
            balance=balance
        )
        
        return {
            "type": "interactive",
            "text": preview_text,
            "buttons": [
                {"id": "confirm_order", "title": "Γ£à Confirm"},
                {"id": "change_qty", "title": "Γ£Å∩╕Å Change Qty"},
                {"id": "cancel_order", "title": "Γ¥î Cancel"}
            ]
        }

    @staticmethod
    async def handle_quantity_input(
        db: AsyncSession, state: ConversationState, user: User, message_text: str
    ) -> list[dict]:
        """Extract number, validate, and move to preview."""
        import re
        match = re.search(r"(\d+(?:\.\d+)?)", message_text)
        if not match:
            return [{"type": "text", "text": get_message("INVALID_QUANTITY", state.language)}]
        
        qty = Decimal(match.group(1))
        if qty <= 0 or qty > 5000:
            return [{"type": "text", "text": get_message("INVALID_QUANTITY", state.language)}]
            
        state.pending_quantity = qty
        await db.commit()
        
        preview_action = await ConversationService.generate_order_preview(db, state, user)
        return [preview_action]

    @staticmethod
    async def process_deterministic_turn(
        db: AsyncSession, state: ConversationState, user: User, message_text: str, button_id: str | None
    ) -> list[dict]:
        """Process turn synchronously when state is NOT IDLE."""
        
        # ΓöÇΓöÇ AWAITING_LANGUAGE ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        if state.state == "AWAITING_LANGUAGE":
            return await ConversationService.handle_language_selection(db, state, user, button_id)

        # ΓöÇΓöÇ AWAITING_PRODUCT ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        if state.state == "AWAITING_PRODUCT":
            product_map = {
                "product_live": "Live Bird",
                "product_dressed": "Dressed",
                "product_skinless": "Skinless"
            }
            if button_id in product_map:
                state.pending_product = product_map[button_id]
                state.state = "AWAITING_QUANTITY"
                await db.commit()
                return [{"type": "text", "text": get_message("ASK_QUANTITY", state.language, product=state.pending_product)}]
            
            # Reprompt
            return [{
                "type": "interactive",
                "text": get_message("ASK_PRODUCT", state.language),
                "buttons": ConversationService.get_product_buttons()
            }]

        # ΓöÇΓöÇ AWAITING_QUANTITY ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        if state.state == "AWAITING_QUANTITY":
            return await ConversationService.handle_quantity_input(db, state, user, message_text)

        # ΓöÇΓöÇ AWAITING_CONFIRMATION ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        if state.state == "AWAITING_CONFIRMATION":
            if button_id == "confirm_order":
                from models.order import Order
                order = Order(
                    tenant_id=state.tenant_id,
                    retailer_id=user.id,
                    phone_number=user.phone,
                    item_type=state.pending_product,
                    quantity_kg=state.pending_quantity,
                    unit_price=state.pending_price_per_kg,
                    total_amount=state.pending_total,
                    status="pending",
                    order_source="whatsapp"
                )
                db.add(order)
                await db.commit()
                await db.refresh(order)
                
                # Perform transition safely via OrderService
                from core.order_service import OrderService
                res = await OrderService.confirm_order(
                    db=db, tenant_id=state.tenant_id, order=order, 
                    unit_price=state.pending_price_per_kg,
                    performed_by=f"WHATSAPP_{user.phone}"
                )
                
                await ConversationService.reset_state(db, state)
                if res.success:
                    return [{"type": "text", "text": get_message("ORDER_CONFIRMED", state.language, order_id=order.id, qty=order.quantity_kg, product=order.item_type)}]
                return [{"type": "text", "text": f"Error: {res.message}"}]
                
            elif button_id == "cancel_order":
                await ConversationService.reset_state(db, state)
                return [{"type": "text", "text": get_message("ORDER_CANCELLED", state.language)}]
                
            elif button_id == "change_qty":
                state.state = "AWAITING_QUANTITY"
                await db.commit()
                return [{"type": "text", "text": get_message("ASK_QUANTITY", state.language, product=state.pending_product)}]
                
            return [await ConversationService.generate_order_preview(db, state, user)]

        # Failsafe
        await ConversationService.reset_state(db, state)
        return [{"type": "text", "text": get_message("RECOVERY_MENU", state.language)}]
