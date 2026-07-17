import logging
import uuid
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text, Sequence

from models.user import User, UserRole
from models.conversation_state import ConversationState
from models.invitation import RetailerInvitation, InviteStatus
from models.onboarding import RetailerOnboardingDraft, DraftStatus, RetailerOnboardingEvent
from core.ai_provider import classify_message
from core.event_broadcaster import broadcast_event
from decimal import Decimal
from core.quote_service import QuoteService, QuoteExpiredError
from core.pricing_service import PricingService
from core.order_service import OrderService
from core.outbox_service import OutboxService
from models.pricing import Quote

logger = logging.getLogger(__name__)

class WhatsAppMessage:
    def __init__(
        self,
        sender_phone: str,
        sender_name: str,
        text: Optional[str] = None,
        button_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ):
        self.sender_phone = sender_phone
        self.sender_name = sender_name
        self.text = (text or "").strip()
        self.button_id = button_id
        self.latitude = latitude
        self.longitude = longitude

    @property
    def is_location(self) -> bool:
        return self.latitude is not None and self.longitude is not None


class ConversationService:
    @staticmethod
    async def get_or_create_state(db: AsyncSession, phone_number: str) -> ConversationState:
        result = await db.execute(
            select(ConversationState)
            .where(ConversationState.phone_number == phone_number)
            .order_by(ConversationState.updated_at.desc())
        )
        state = result.scalars().first()
        if not state:
            state = ConversationState(
                phone_number=phone_number,
                state="READY",
                language=None
            )
            db.add(state)
            await db.commit()
            await db.refresh(state)
        return state

    @classmethod
    async def process(cls, db: AsyncSession, message: WhatsAppMessage, user: Optional[User] = None) -> List[Dict[str, Any]]:
        state = await cls.get_or_create_state(db, message.sender_phone)
        
        # Sync user and tenant IDs if user exists
        if user and (state.user_id != user.id or state.tenant_id != user.tenant_id):
            state.user_id = user.id
            state.tenant_id = user.tenant_id
            await db.commit()
        
        # 1. Global Interrupt Layer
        emergency_action = await cls._handle_emergency(db, state, message)
        if emergency_action:
            return emergency_action

        # 2. Check Timeouts
        timeout_action = await cls._handle_timeout(db, state)
        if timeout_action:
            return timeout_action
            
        # 3. Handle JOIN_GC Deep Links
        if message.text.startswith("JOIN_GC_"):
            return await cls._handle_invite(db, state, message, user)
            
        # If no active onboarding, and user doesn't exist, we must drop them
        # unless they are clicking JOIN_GC.
        if not user and state.state == "READY":
            return [{"type": "text", "text": "Welcome to Go Chicken. Please ask your wholesaler for an invitation QR code to register."}]
            
        if user and user.onboarding_status == "PENDING_APPROVAL" and state.state == "WAITING_APPROVAL":
            return [{"type": "text", "text": "Your registration is currently pending wholesaler approval.\n\nWe'll notify you as soon as your account is activated."}]

        # 4. Route based on state
        handler = cls._get_state_handler(state.state)
        return await handler(db, state, message, user)

    @classmethod
    async def _handle_emergency(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage) -> Optional[List[Dict[str, Any]]]:
        text_lower = message.text.lower()
        if text_lower in ["cancel", "stop", "abort"]:
            state.state = "READY"
            
            # Find active draft and abandon
            draft_res = await db.execute(
                select(RetailerOnboardingDraft)
                .where(
                    RetailerOnboardingDraft.phone_number == message.sender_phone,
                    RetailerOnboardingDraft.status == DraftStatus.IN_PROGRESS
                )
                .order_by(RetailerOnboardingDraft.created_at.desc())
            )
            draft = draft_res.scalars().first()
            if draft:
                draft.status = DraftStatus.ABANDONED
                
            await db.commit()
            return [{"type": "text", "text": "Operation cancelled. We've returned to the main menu."}]
            
        if text_lower == "restart" and state.state.startswith("ONBOARDING"):
            state.state = "ONBOARDING_LANGUAGE"
            # Abandon existing draft
            draft_res = await db.execute(
                select(RetailerOnboardingDraft)
                .where(
                    RetailerOnboardingDraft.phone_number == message.sender_phone,
                    RetailerOnboardingDraft.status == DraftStatus.IN_PROGRESS
                )
                .order_by(RetailerOnboardingDraft.created_at.desc())
            )
            draft = draft_res.scalars().first()
            if draft:
                draft.status = DraftStatus.ABANDONED
            
            await db.commit()
            return [{"type": "interactive", "text": "Let's start over.\n\nPlease select your preferred language:", "buttons": [{"id": "lang_en", "title": "English"}, {"id": "lang_hi", "title": "Hindi"}, {"id": "lang_te", "title": "Telugu"}]}]
            
        if text_lower in ["help", "support", "talk to boss"]:
            # Could set state to SUPPORT, but for now just show message
            return [{"type": "text", "text": "Support requested. A Go Chicken representative will contact you shortly."}]
            
        return None

    @classmethod
    async def _handle_timeout(cls, db: AsyncSession, state: ConversationState) -> Optional[List[Dict[str, Any]]]:
        now = datetime.now(timezone.utc)
        
        if state.state.startswith("AWAITING_"):
            # Ensure it is timezone aware
            updated = state.updated_at.replace(tzinfo=timezone.utc) if state.updated_at.tzinfo is None else state.updated_at
            if updated and now - updated > timedelta(hours=24):
                state.state = "READY"
                state.pending_product = None
                state.pending_quantity = None
                state.pending_quote_id = None
                await db.commit()
                return [{"type": "text", "text": "Order session expired due to inactivity. You can start a new order anytime."}]
                
        if not state.state.startswith("ONBOARDING"):
            return None
            
        draft_res = await db.execute(
            select(RetailerOnboardingDraft)
            .where(
                RetailerOnboardingDraft.phone_number == state.phone_number,
                RetailerOnboardingDraft.status == DraftStatus.IN_PROGRESS
            )
            .order_by(RetailerOnboardingDraft.created_at.desc())
        )
        draft = draft_res.scalars().first()
        
        if draft:
            # 24 hour check
            updated = draft.updated_at.replace(tzinfo=timezone.utc) if draft.updated_at.tzinfo is None else draft.updated_at
            if now - updated > timedelta(hours=24):
                draft.status = DraftStatus.ABANDONED
                state.state = "READY"
                await db.commit()
                return [{"type": "text", "text": "Registration expired due to inactivity. Please scan your QR code again to restart."}]
                
        return None

    @classmethod
    async def _handle_invite(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage, user: Optional[User]) -> List[Dict[str, Any]]:
        # Session Lock (Active Draft)
        if state.state != "READY":
            return [{"type": "text", "text": "Please finish your current registration first. (Type 'cancel' to restart)"}]
            
        if user:
            if user.onboarding_status == "ACTIVE":
                return [{"type": "text", "text": "Welcome back! Your number is already registered. If you need to change wholesalers, please contact your current wholesaler."}]
            elif user.onboarding_status == "PENDING_APPROVAL":
                state.state = "WAITING_APPROVAL"
                await db.commit()
                return [{"type": "text", "text": "Your registration is currently pending wholesaler approval."}]

        invite_code = message.text.replace("JOIN_GC_", "").strip()
        
        # Validate Invite
        inv_res = await db.execute(select(RetailerInvitation).where(RetailerInvitation.invite_code == invite_code))
        invite = inv_res.scalar_one_or_none()
        
        if not invite:
            return [{"type": "text", "text": "This invitation is invalid. Please contact your wholesaler."}]
            
        if invite.status == InviteStatus.EXPIRED:
            return [{"type": "text", "text": "This invitation has expired. Please ask your wholesaler to generate a new invitation."}]
            
        if invite.expires_at:
            exp = invite.expires_at.replace(tzinfo=timezone.utc) if invite.expires_at.tzinfo is None else invite.expires_at
            if exp < datetime.now(timezone.utc):
                return [{"type": "text", "text": "This invitation has expired. Please ask your wholesaler to generate a new invitation."}]
            
        if invite.status == InviteStatus.USED:
            return [{"type": "text", "text": "This invitation has already been used. Contact your wholesaler."}]
            
        if invite.status == InviteStatus.CANCELLED:
            return [{"type": "text", "text": "This invitation is no longer valid. Contact your wholesaler."}]
            
        # Create new Draft
        draft = RetailerOnboardingDraft(
            phone_number=message.sender_phone,
            invite_id=invite.id,
            tenant_id=invite.tenant_id,
            owner_name=message.sender_name, # Default to whatsapp name
            status=DraftStatus.IN_PROGRESS
        )
        db.add(draft)
        await db.flush() # flush to get draft.id
        
        db.add(RetailerOnboardingEvent(
            draft_id=draft.id,
            event="INVITE_OPENED"
        ))
        
        # Mark invite opened
        invite.status = InviteStatus.OPENED
        
        # Update State
        state.state = "ONBOARDING_LANGUAGE"
        await db.commit()
        
        return [{"type": "interactive", "text": "Welcome to Go Chicken Registration!\n\nPlease select your preferred language:", "buttons": [{"id": "lang_en", "title": "English"}, {"id": "lang_hi", "title": "Hindi"}, {"id": "lang_te", "title": "Telugu"}]}]

    @classmethod
    def _get_state_handler(cls, current_state: str):
        handlers = {
            "READY": cls._handle_ready_state,
            "WAITING_APPROVAL": cls._handle_waiting_approval,
            "ONBOARDING_LANGUAGE": cls._handle_onboarding_language,
            "ONBOARDING_NAME": cls._handle_onboarding_name,
            "ONBOARDING_LOCATION": cls._handle_onboarding_location,
            "ONBOARDING_SHOP": cls._handle_onboarding_shop,
            "ONBOARDING_REVIEW": cls._handle_onboarding_review,
            "AWAITING_PRODUCT": cls._handle_awaiting_product,
            "AWAITING_QUANTITY": cls._handle_awaiting_quantity,
            "AWAITING_CONFIRMATION": cls._handle_awaiting_confirmation,
        }
        return handlers.get(current_state, cls._handle_ready_state)
        
    @classmethod
    async def _handle_waiting_approval(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage, user: Optional[User]) -> List[Dict[str, Any]]:
        return [{"type": "text", "text": "Your registration is currently pending wholesaler approval.\n\nWe'll notify you as soon as your account is activated."}]

    @classmethod
    async def _get_active_draft(cls, db: AsyncSession, phone: str) -> RetailerOnboardingDraft:
        draft_res = await db.execute(
            select(RetailerOnboardingDraft)
            .where(
                RetailerOnboardingDraft.phone_number == phone,
                RetailerOnboardingDraft.status == DraftStatus.IN_PROGRESS
            )
            .order_by(RetailerOnboardingDraft.created_at.desc())
        )
        return draft_res.scalars().first()

    @classmethod
    async def _handle_onboarding_language(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage, user: Optional[User]) -> List[Dict[str, Any]]:
        draft = await cls._get_active_draft(db, state.phone_number)
        if not draft:
            state.state = "READY"
            await db.commit()
            return [{"type": "text", "text": "No active registration found. Please scan your QR code."}]
            
        lang = None
        if message.button_id == "lang_en" or message.text.lower() == "english":
            lang = "en"
        elif message.button_id == "lang_hi" or message.text.lower() == "hindi":
            lang = "hi"
        elif message.button_id == "lang_te" or message.text.lower() == "telugu":
            lang = "te"
            
        if not lang:
            return [{"type": "interactive", "text": "I didn't understand that. Please select your language:", "buttons": [{"id": "lang_en", "title": "English"}, {"id": "lang_hi", "title": "Hindi"}, {"id": "lang_te", "title": "Telugu"}]}]
            
        draft.preferred_language = lang
        state.language = lang
        state.state = "ONBOARDING_NAME"
        draft.updated_at = datetime.now(timezone.utc)
        db.add(RetailerOnboardingEvent(
            draft_id=draft.id,
            event="LANGUAGE_SELECTED",
            metadata_payload={"language": lang}
        ))
        await db.commit()
        
        # Proceed to next question
        return [{"type": "text", "text": "Great! What is your full name? (e.g. Ravi Kumar)"}]

    @classmethod
    async def _handle_onboarding_name(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage, user: Optional[User]) -> List[Dict[str, Any]]:
        draft = await cls._get_active_draft(db, state.phone_number)
        
        # Validation: Must not be only numbers/symbols
        if not message.text or not re.search(r'[a-zA-Z]', message.text):
            return [{"type": "text", "text": "Please enter a valid name containing letters."}]
            
        draft.owner_name = message.text
        state.state = "ONBOARDING_LOCATION"
        draft.updated_at = datetime.now(timezone.utc)
        db.add(RetailerOnboardingEvent(
            draft_id=draft.id,
            event="NAME_ENTERED",
            metadata_payload={"name": message.text}
        ))
        await db.commit()
        
        return [{"type": "text", "text": f"Thanks, {message.text}.\n\nPlease share your shop's location using the WhatsApp attachment (📍 Share Location)."}]

    @classmethod
    async def _handle_onboarding_location(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage, user: Optional[User]) -> List[Dict[str, Any]]:
        draft = await cls._get_active_draft(db, state.phone_number)
        
        if not message.is_location:
            return [{"type": "text", "text": "To continue registration, please share your location.\n\n📍 Tap the attachment icon (📎) and select 'Location'."}]
            
        draft.latitude = message.latitude
        draft.longitude = message.longitude
        state.state = "ONBOARDING_SHOP"
        draft.updated_at = datetime.now(timezone.utc)
        db.add(RetailerOnboardingEvent(
            draft_id=draft.id,
            event="LOCATION_SHARED",
            metadata_payload={"lat": float(message.latitude), "lon": float(message.longitude)}
        ))
        await db.commit()
        
        return [{"type": "text", "text": "Location saved! What is the name of your shop? (e.g. Sri Lakshmi Chicken Center)"}]

    @classmethod
    async def _handle_onboarding_shop(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage, user: Optional[User]) -> List[Dict[str, Any]]:
        draft = await cls._get_active_draft(db, state.phone_number)
        
        if not message.text or len(message.text) < 3:
            return [{"type": "text", "text": "Shop name is too short. Please enter the full name of your shop."}]
            
        draft.shop_name = message.text
        state.state = "ONBOARDING_REVIEW"
        draft.updated_at = datetime.now(timezone.utc)
        db.add(RetailerOnboardingEvent(
            draft_id=draft.id,
            event="SHOP_ENTERED",
            metadata_payload={"shop_name": message.text}
        ))
        await db.commit()
        
        summary = (
            f"Please review your details:\n\n"
            f"👤 Owner: {draft.owner_name}\n"
            f"🏪 Shop: {draft.shop_name}\n"
            f"🌐 Language: {draft.preferred_language}\n"
            f"📍 Location: Saved ✓\n\n"
            f"Is this correct?"
        )
        return [{"type": "interactive", "text": summary, "buttons": [{"id": "btn_confirm", "title": "Submit Registration"}, {"id": "btn_edit", "title": "Restart Flow"}]}]

    @classmethod
    async def _handle_onboarding_review(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage, user: Optional[User]) -> List[Dict[str, Any]]:
        draft = await cls._get_active_draft(db, state.phone_number)
        
        if message.button_id == "btn_edit" or message.text.lower() == "restart":
            state.state = "ONBOARDING_LANGUAGE"
            draft.updated_at = datetime.now(timezone.utc)
            await db.commit()
            return [{"type": "interactive", "text": "Let's try again.\n\nPlease select your preferred language:", "buttons": [{"id": "lang_en", "title": "English"}, {"id": "lang_hi", "title": "Hindi"}, {"id": "lang_te", "title": "Telugu"}]}]
            
        if message.button_id == "btn_confirm" or message.text.lower() == "submit":
            # Idempotency check: see if user was already created (e.g. Meta retried)
            existing_user_res = await db.execute(select(User).where(User.phone == draft.phone_number))
            existing_user = existing_user_res.scalar_one_or_none()
            
            if existing_user:
                # If they already exist and we got a duplicate confirm webhook, just return the exact same success message
                # Don't recreate the user.
                state.state = "WAITING_APPROVAL"
                await db.commit()
                msg = (
                    f"Registration Submitted\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"Retailer ID\n"
                    f"{existing_user.retailer_id}\n\n"
                    f"Status\n"
                    f"Pending Approval\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"You will receive a WhatsApp notification once approved."
                )
                return [{"type": "text", "text": msg}]
        
            # Fetch atomic sequence ID
            seq_val = await db.scalar(text("SELECT nextval('retailer_id_seq')"))
            retailer_id = f"GC-RET-{seq_val:06d}"

            # 1. Create User
            new_user = User(
                phone=draft.phone_number,
                whatsapp_id=draft.phone_number,
                role=UserRole.RETAILER,
                tenant_id=draft.tenant_id,
                name=draft.owner_name,
                shop_name=draft.shop_name,
                preferred_language=draft.preferred_language,
                onboarding_status="PENDING_APPROVAL",
                retailer_id=retailer_id
            )
            db.add(new_user)
            
            # 2. Update Draft & Invite & Add Event
            draft.status = DraftStatus.COMPLETED
            draft.updated_at = datetime.now(timezone.utc)
            
            db.add(RetailerOnboardingEvent(
                draft_id=draft.id,
                event="SUBMITTED"
            ))
            
            inv_res = await db.execute(select(RetailerInvitation).where(RetailerInvitation.id == draft.invite_id))
            invite = inv_res.scalar_one_or_none()
            if invite:
                invite.status = InviteStatus.USED
                invite.used_at = datetime.now(timezone.utc)
            
            state.state = "WAITING_APPROVAL"
            await db.commit()
            
            # 3. Fire SSE
            await broadcast_event("NEW_RETAILER_REGISTRATION", {
                "retailer_name": draft.owner_name,
                "shop_name": draft.shop_name,
                "phone": draft.phone_number
            })
            
            # 4. Return Killer Feature Progress
            msg = (
                f"Registration Submitted\n"
                f"━━━━━━━━━━━━━━\n"
                f"Retailer ID\n"
                f"{new_user.retailer_id}\n\n"
                f"Status\n"
                f"Pending Approval\n"
                f"━━━━━━━━━━━━━━\n"
                f"You will receive a WhatsApp notification once approved.\n\n"
                f"Current Progress\n"
                f"✅ Language\n"
                f"✅ Name\n"
                f"✅ Location\n"
                f"✅ Shop\n"
                f"⏳ Approval"
            )
            return [{"type": "text", "text": msg}]
            
        return [{"type": "interactive", "text": "I didn't understand. Please confirm your details.", "buttons": [{"id": "btn_confirm", "title": "Submit Registration"}, {"id": "btn_edit", "title": "Restart Flow"}]}]

    @classmethod
    async def _handle_ready_state(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage, user: Optional[User]) -> List[Dict[str, Any]]:
        # Button Overrides
        if message.button_id == "menu_order":
            return await cls._advance_order_state(db, state, user)
        elif message.button_id == "menu_prices":
            return [{"type": "text", "text": "🐔 Live Bird: ₹180/kg\n🍗 Dressed: ₹250/kg\n🥩 Skinless: ₹320/kg"}]
            
        if not message.text:
            return cls._build_recovery_menu()
            
        # Use AI Intent Classification
        classification = await classify_message(message.text)
        
        if not classification or classification.confidence < 0.8:
            return cls._build_recovery_menu()
            
        return await cls._execute_intent(db, classification, state, user)
        
    @classmethod
    def _build_recovery_menu(cls) -> List[Dict[str, Any]]:
        msg = "I didn't understand. Choose one:"
        buttons = [
            {"id": "menu_order", "title": "📦 Place Order"},
            {"id": "menu_prices", "title": "💰 Today's Prices"},
            {"id": "menu_khata", "title": "💳 Khata"}
        ]
        return [{"type": "interactive", "text": msg, "buttons": buttons}]

    @classmethod
    def _normalize_product(cls, product_name: str) -> Optional[str]:
        if not product_name:
            return None
        norm = product_name.lower()
        if any(x in norm for x in ["live", "broiler", "lb", "live bird"]):
            return "BROILER"
        elif any(x in norm for x in ["dress", "desi"]):
            return "DESI"
        elif any(x in norm for x in ["skinless", "layer", "layer bird"]):
            return "LAYER"
        return product_name

    @classmethod
    async def _execute_intent(cls, db: AsyncSession, classification, state: ConversationState, user: Optional[User]) -> List[Dict[str, Any]]:
        intent = classification.intent
        
        if intent == "ORDER":
            if classification.item:
                state.pending_product = cls._normalize_product(classification.item)
            if classification.quantity_kg and classification.quantity_kg > 0:
                state.pending_quantity = Decimal(str(classification.quantity_kg))
            
            await db.commit()
            return await cls._advance_order_state(db, state, user)
            
        elif intent == "PRICE_INQUIRY":
            return [{"type": "text", "text": "🐔 BROILER: ₹155/kg\n🍗 DESI: ₹210/kg\n🥩 LAYER: ₹130/kg"}]
        elif intent == "GREETING":
            return cls._build_recovery_menu()
        elif intent == "KHATA":
            return [{"type": "text", "text": "Mock: Your current balance is ₹0.00"}]
        else:
            return cls._build_recovery_menu()

    @classmethod
    async def _advance_order_state(cls, db: AsyncSession, state: ConversationState, user: User) -> List[Dict[str, Any]]:
        if not state.pending_product:
            state.state = "AWAITING_PRODUCT"
            await db.commit()
            return [{
                "type": "interactive", 
                "text": "Which product would you like to order?", 
                "buttons": [
                    {"id": "prod_broiler", "title": "🐔 BROILER"},
                    {"id": "prod_desi", "title": "🍗 DESI"},
                    {"id": "prod_layer", "title": "🥩 LAYER"}
                ]
            }]
            
        if not state.pending_quantity:
            state.state = "AWAITING_QUANTITY"
            await db.commit()
            return [{"type": "text", "text": f"How many KG of {state.pending_product} do you need?"}]
            
        # Both exist, create quote snapshot
        pricing_service = PricingService()
        quote_service = QuoteService(pricing_service)
        
        quote = await quote_service.create_quote(
            db=db,
            tenant_id=state.tenant_id,
            customer_id=user.id,
            quote_number=f"QT-{uuid.uuid4().hex[:8].upper()}",
            items_input=[{
                "sku": state.pending_product,
                "quantity_kg": state.pending_quantity
            }],
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            commit=True
        )
        
        state.pending_quote_id = quote.id
        state.state = "AWAITING_CONFIRMATION"
        await db.commit()
        
        # Format the Preview Card
        total_amt = f"{quote.total_amount:,.2f}"
        rate = f"{(quote.total_amount / state.pending_quantity):,.2f}"
        
        msg = (
            f"📦 *Quote Preview*\n"
            f"━━━━━━━━━━━━━━\n"
            f"Product: {state.pending_product}\n"
            f"Quantity: {state.pending_quantity} KG\n"
            f"Rate: ₹{rate}/KG\n"
            f"Total: *₹{total_amt}*\n"
            f"━━━━━━━━━━━━━━\n"
        )
        
        return [{
            "type": "interactive", 
            "text": msg, 
            "buttons": [
                {"id": "btn_confirm_order", "title": "✅ Confirm"},
                {"id": "btn_cancel_order", "title": "❌ Cancel"}
            ]
        }]

    @classmethod
    async def _handle_awaiting_product(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage, user: Optional[User]) -> List[Dict[str, Any]]:
        # If user typed something instead of clicking button, maybe AI can extract it
        if message.text and not message.button_id:
            classification = await classify_message(message.text)
            if classification and classification.item:
                state.pending_product = cls._normalize_product(classification.item)
            if classification and classification.quantity_kg and classification.quantity_kg > 0:
                state.pending_quantity = Decimal(str(classification.quantity_kg))
        else:
            prod_map = {"prod_broiler": "BROILER", "prod_desi": "DESI", "prod_layer": "LAYER"}
            if message.button_id in prod_map:
                state.pending_product = prod_map[message.button_id]

        if not state.pending_product:
            return [{
                "type": "interactive", 
                "text": "Please choose a product:", 
                "buttons": [
                    {"id": "prod_broiler", "title": "🐔 BROILER"},
                    {"id": "prod_desi", "title": "🍗 DESI"},
                    {"id": "prod_layer", "title": "🥩 LAYER"}
                ]
            }]
            
        await db.commit()
        return await cls._advance_order_state(db, state, user)

    @classmethod
    async def _handle_awaiting_quantity(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage, user: Optional[User]) -> List[Dict[str, Any]]:
        if message.button_id == "btn_cancel_order":
            state.state = "READY"
            state.pending_product = None
            state.pending_quantity = None
            await db.commit()
            return [{"type": "text", "text": "Order cancelled."}]
            
        text_val = message.text
        match = re.search(r"(\d+(?:\.\d+)?)", text_val)
        if not match:
            return [{"type": "text", "text": "Please enter a valid number for quantity (e.g., 50 or 12.5):"}]
            
        qty = Decimal(match.group(1))
        if qty <= 0 or qty > 5000:
            return [{"type": "text", "text": "Please enter a valid quantity between 1 and 5000 KG:"}]
            
        state.pending_quantity = qty
        await db.commit()
        return await cls._advance_order_state(db, state, user)

    @classmethod
    async def _handle_awaiting_confirmation(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage, user: Optional[User]) -> List[Dict[str, Any]]:
        # If user types something like 'Need 100kg' while we're awaiting confirmation
        if message.text and not message.button_id:
            return [{
                "type": "interactive",
                "text": "You already have a pending quote preview. Please Confirm or Cancel it first.",
                "buttons": [
                    {"id": "btn_confirm_order", "title": "✅ Confirm"},
                    {"id": "btn_cancel_order", "title": "❌ Cancel"}
                ]
            }]

        if message.button_id == "btn_cancel_order":
            state.state = "READY"
            state.pending_product = None
            state.pending_quantity = None
            state.pending_quote_id = None
            await db.commit()
            return [{"type": "text", "text": "Order cancelled."}]
            
        if message.button_id == "btn_confirm_order":
            if not state.pending_quote_id:
                return await cls._advance_order_state(db, state, user)
                
            pricing_service = PricingService()
            quote_service = QuoteService(pricing_service)
            outbox_service = OutboxService()
            
            try:
                # This will raise QuoteExpiredError if expired
                quote = await quote_service.convert_to_order(
                    db=db,
                    tenant_id=state.tenant_id,
                    quote_id=state.pending_quote_id,
                    outbox_service=outbox_service,
                    commit=True
                )
                
                state.state = "READY"
                state.pending_product = None
                state.pending_quantity = None
                state.pending_quote_id = None
                await db.commit()
                
                return [{"type": "text", "text": f"🎉 *Order Confirmed!*\nOrder ID: {quote.quote_number}\n{state.pending_quantity}kg {state.pending_product} locked in. 🚛✅"}]
                
            except QuoteExpiredError:
                # Clear quote and regenerate
                state.pending_quote_id = None
                await db.commit()
                
                msgs = [{"type": "text", "text": "This quotation has expired. Generating latest pricing..."}]
                msgs.extend(await cls._advance_order_state(db, state, user))
                return msgs
                
            except Exception as e:
                logger.error(f"Order confirmation failed: {e}")
                return [{"type": "text", "text": "Failed to confirm order. Please try again."}]
                
        return await cls._advance_order_state(db, state, user)
