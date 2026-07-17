import uuid
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import urllib.parse
from decimal import Decimal

from core.database import get_db
from core.config import get_settings
from models.user import User, UserRole
from models.tenant import Tenant
from models.invitation import RetailerInvitation, InviteSource, InviteStatus
from models.onboarding import RetailerOnboardingDraft, DraftStatus, RetailerOnboardingEvent
from models.khata import KhataLedger
from models.pricing import PriceBook
from core.event_broadcaster import broadcast_event
import random
import string

router = APIRouter(prefix="/retailers", tags=["retailers"])

def generate_invite_code(length=6) -> str:
    """Generate a random alphanumeric invite code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class InviteRequest(BaseModel):
    source: InviteSource = InviteSource.QR_DASHBOARD
    expires_in_hours: int = 24

class InviteResponse(BaseModel):
    invite_id: uuid.UUID
    invite_code: str
    qr_url: str
    expires_at: datetime
    status: str

@router.post("/invite", response_model=InviteResponse)
async def create_invite(
    req: InviteRequest = None, 
    db: AsyncSession = Depends(get_db)
):
    """Generate a new onboarding invite and return data + QR URL."""
    req = req or InviteRequest()
    # For hackathon demo, assuming tenant is the first one in DB
    result = await db.execute(select(Tenant).limit(1))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=400, detail="No tenant found.")

    invite_code = generate_invite_code()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=req.expires_in_hours)

    invite = RetailerInvitation(
        tenant_id=tenant.id,
        invite_code=invite_code,
        source=req.source,
        status=InviteStatus.GENERATED,
        expires_at=expires_at
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)

    settings = get_settings()
    whatsapp_bot_number = getattr(settings, "WHATSAPP_BOT_PHONE_NUMBER", "15551701265") # Fallback to Meta Test Number
    message = urllib.parse.quote(f"JOIN_GC_{invite_code}")
    qr_url = f"https://wa.me/{whatsapp_bot_number}?text={message}"

    return InviteResponse(
        invite_id=invite.id,
        invite_code=invite_code,
        qr_url=qr_url,
        expires_at=invite.expires_at,
        status=invite.status.value
    )

@router.get("/pending")
async def get_pending_retailers(db: AsyncSession = Depends(get_db)):
    """Fetch all retailers pending approval with mocked AI/distance metrics."""
    result = await db.execute(
        select(User).where(
            User.role == UserRole.RETAILER,
            User.onboarding_status == "PENDING_APPROVAL"
        )
    )
    pending_users = result.scalars().all()
    
    response = []
    for user in pending_users:
        # Mocking Haversine / AI Demand for Hackathon
        response.append({
            "id": user.id,
            "owner_name": user.name,
            "shop_name": user.shop_name,
            "phone": user.phone,
            "preferred_language": user.preferred_language,
            "retailer_id": user.retailer_id,
            "registration_time": user.created_at,
            # Hackathon Deterministic Mocks
            "distance_km": round(2.3 + (hash(user.id) % 10) / 10, 1),
            "suggested_zone": "East Zone",
            "suggested_credit": 50000.00,
            "expected_weekly_demand_kg": 320 + (hash(user.id) % 50),
            "whatsapp_verified": True,
            "timeline": [] # Will populate below
        })
        
    # Batch fetch drafts and events
    if pending_users:
        phones = [u.phone for u in pending_users]
        drafts_res = await db.execute(
            select(RetailerOnboardingDraft, RetailerOnboardingEvent)
            .join(RetailerOnboardingEvent, RetailerOnboardingEvent.draft_id == RetailerOnboardingDraft.id)
            .where(RetailerOnboardingDraft.phone_number.in_(phones))
            .order_by(RetailerOnboardingEvent.timestamp.asc())
        )
        
        events_by_phone = {}
        for draft, event in drafts_res.all():
            if draft.phone_number not in events_by_phone:
                events_by_phone[draft.phone_number] = []
            events_by_phone[draft.phone_number].append({
                "event": event.event,
                "timestamp": event.timestamp.isoformat(),
                "metadata": event.metadata_payload
            })
            
        for r in response:
            if r["phone"] in events_by_phone:
                r["timeline"] = events_by_phone[r["phone"]]

    return response

class ApproveRequest(BaseModel):
    credit_limit: Decimal
    price_book_id: Optional[uuid.UUID] = None
    zone: str

@router.put("/{user_id}/approve")
async def approve_retailer(
    user_id: uuid.UUID, 
    req: ApproveRequest,
    db: AsyncSession = Depends(get_db)
):
    """Atomically approve a retailer, creating Khata and setting pricing."""
    result = await db.execute(select(User).where(User.id == user_id, User.onboarding_status == "PENDING_APPROVAL"))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Pending retailer not found.")
        
    try:
        # 1. Update User Status
        user.onboarding_status = "ACTIVE"
        user.zone = req.zone
        
        # 2. Create Khata Ledger Projection
        from models.khata import CustomerBalanceProjection
        existing_khata = await db.execute(select(CustomerBalanceProjection).where(
            CustomerBalanceProjection.tenant_id == user.tenant_id,
            CustomerBalanceProjection.customer_id == user.id
        ))
        if not existing_khata.scalar_one_or_none():
            khata = CustomerBalanceProjection(
                tenant_id=user.tenant_id,
                customer_id=user.id,
                outstanding_balance=0
            )
            db.add(khata)
        
        # 3. Assign Default Price Book (Mocked logic if no book passed)
        if not req.price_book_id:
            book_res = await db.execute(select(PriceBook).where(PriceBook.tenant_id == user.tenant_id).limit(1))
            book = book_res.scalar_one_or_none()
            if book:
                pass # Typically would link price book to user profile here. For now assumed attached.
                
        # 4. Reset Conversation State to READY
        from models.communication import ConversationState
        state_res = await db.execute(select(ConversationState).where(ConversationState.phone_number == user.phone))
        conv_state = state_res.scalar_one_or_none()
        if conv_state:
            conv_state.state = "READY"

        await db.commit()
        await db.refresh(user)
        
        # Trigger Welcome Message
        from routers.whatsapp import _send_whatsapp_reply
        
        welcome_msg = (
            f"🎉 Congratulations!\n\n"
            f"Your Go Chicken account is now active.\n\n"
            f"Retailer ID:\n{user.retailer_id}\n\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"You can now:\n\n"
            f"📦 Place Orders\n"
            f"💰 Check Today's Rates\n"
            f"📄 Track Orders\n"
            f"💳 View Khata\n\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"Type \"Menu\" anytime to see available options."
        )
        
        phone_number_id = "your-phone-id" # Typically fetched from config or tenant
        # Since we're sending asynchronously outside webhook, we would normally enqueue this.
        # For hackathon, just send if we know the phone_number_id. Assuming standard test ID or hardcode.
        from core.config import get_settings
        settings = get_settings()
        if settings.WHATSAPP_API_TOKEN:
             import asyncio
             # Send the welcome message asynchronously
             phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID or "your-phone-id"
             asyncio.create_task(_send_whatsapp_reply(
                 phone_number_id=phone_number_id,
                 to=user.phone,
                 message=welcome_msg
             ))
        
        # We will mock the WhatsApp API call here for the hackathon UI
        # We can just broadcast the event so the UI knows.
        from core.event_broadcaster import broadcast_event
        await broadcast_event("RETAILER_APPROVED", {
            "retailer_id": user.retailer_id,
            "phone": user.phone,
            "message": welcome_msg,
            "shop_name": user.shop_name
        })
        
        return {"status": "success", "retailer_id": user.retailer_id, "message": "Retailer approved and activated."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")

@router.post("/{user_id}/reject")
async def reject_retailer(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Reject a retailer registration."""
    result = await db.execute(select(User).where(User.id == user_id, User.onboarding_status == "PENDING_APPROVAL"))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Pending retailer not found.")
        
    try:
        user.onboarding_status = "REJECTED"
        
        # Reset Conversation State to READY
        from models.communication import ConversationState
        state_res = await db.execute(select(ConversationState).where(ConversationState.phone_number == user.phone))
        conv_state = state_res.scalar_one_or_none()
        if conv_state:
            conv_state.state = "READY"
            
        await db.commit()
        
        reject_msg = (
            f"Your registration for Go Chicken has been declined.\n\n"
            f"If you believe this is a mistake, please contact your wholesaler."
        )
        
        from core.event_broadcaster import broadcast_event
        await broadcast_event("RETAILER_REJECTED", {
            "user_id": str(user.id),
            "phone": user.phone,
            "message": reject_msg
        })
        
        return {"status": "success", "message": "Retailer rejected successfully."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Rejection failed: {str(e)}")
