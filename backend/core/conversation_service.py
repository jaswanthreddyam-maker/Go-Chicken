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
        result = await db.execute(select(ConversationState).where(ConversationState.phone_number == phone_number))
        state = result.scalar_one_or_none()
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
            draft_res = await db.execute(select(RetailerOnboardingDraft).where(
                RetailerOnboardingDraft.phone_number == message.sender_phone,
                RetailerOnboardingDraft.status == DraftStatus.IN_PROGRESS
            ))
            draft = draft_res.scalar_one_or_none()
            if draft:
                draft.status = DraftStatus.ABANDONED
                
            await db.commit()
            return [{"type": "text", "text": "Operation cancelled. We've returned to the main menu."}]
            
        if text_lower == "restart" and state.state.startswith("ONBOARDING"):
            state.state = "ONBOARDING_LANGUAGE"
            # Abandon existing draft
            draft_res = await db.execute(select(RetailerOnboardingDraft).where(
                RetailerOnboardingDraft.phone_number == message.sender_phone,
                RetailerOnboardingDraft.status == DraftStatus.IN_PROGRESS
            ))
            draft = draft_res.scalar_one_or_none()
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
        if not state.state.startswith("ONBOARDING"):
            return None
            
        draft_res = await db.execute(select(RetailerOnboardingDraft).where(
            RetailerOnboardingDraft.phone_number == state.phone_number,
            RetailerOnboardingDraft.status == DraftStatus.IN_PROGRESS
        ))
        draft = draft_res.scalar_one_or_none()
        
        if draft:
            # 24 hour check
            if datetime.now(timezone.utc) - draft.updated_at > timedelta(hours=24):
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
            
        if invite.status == InviteStatus.EXPIRED or (invite.expires_at and invite.expires_at < datetime.now(timezone.utc)):
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
        }
        return handlers.get(current_state, cls._handle_ready_state)
        
    @classmethod
    async def _handle_waiting_approval(cls, db: AsyncSession, state: ConversationState, message: WhatsAppMessage, user: Optional[User]) -> List[Dict[str, Any]]:
        return [{"type": "text", "text": "Your registration is currently pending wholesaler approval.\n\nWe'll notify you as soon as your account is activated."}]

    @classmethod
    async def _get_active_draft(cls, db: AsyncSession, phone: str) -> RetailerOnboardingDraft:
        draft_res = await db.execute(select(RetailerOnboardingDraft).where(
            RetailerOnboardingDraft.phone_number == phone,
            RetailerOnboardingDraft.status == DraftStatus.IN_PROGRESS
        ))
        return draft_res.scalar_one_or_none()

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
            return [{"type": "text", "text": "Mock: Start order flow."}] # Placeholder for actual order logic
        elif message.button_id == "menu_prices":
            return [{"type": "text", "text": "🐔 Live Bird: ₹180/kg\n🍗 Dressed: ₹250/kg\n🥩 Skinless: ₹320/kg"}]
            
        if not message.text:
            return cls._build_recovery_menu()
            
        # Use AI Intent Classification
        classification = await classify_message(message.text)
        
        if not classification or classification.confidence < 0.8:
            return cls._build_recovery_menu()
            
        return await cls._execute_intent(classification, state, user)
        
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
    async def _execute_intent(cls, classification, state: ConversationState, user: Optional[User]) -> List[Dict[str, Any]]:
        intent = classification.intent
        
        if intent == "ORDER":
            return [{"type": "text", "text": f"Mock: Placing order for {classification.quantity_kg}kg {classification.item}"}]
        elif intent == "PRICE_INQUIRY":
            return [{"type": "text", "text": "🐔 Live Bird: ₹180/kg\n🍗 Dressed: ₹250/kg\n🥩 Skinless: ₹320/kg"}]
        elif intent == "GREETING":
            return cls._build_recovery_menu()
        elif intent == "KHATA":
            return [{"type": "text", "text": "Mock: Your current balance is ₹0.00"}]
        else:
            return cls._build_recovery_menu()
