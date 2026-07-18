import uuid
import io
import csv
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import get_db
from core.auth import get_current_tenant
from core.cloudinary_service import upload_profile_picture
from models.profile import BusinessProfile
from models.khata import KhataTransaction
from models.order import Order
from schemas.profile import ProfileResponse, ProfileUpdate

router = APIRouter(
    prefix="/api/v1/profile",
    tags=["Profile"]
)

@router.get("", response_model=ProfileResponse)
@router.get("/", response_model=ProfileResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant)
):
    """Fetch the business profile and user identity for the currently authenticated tenant."""
    try:
        from models.user import User, UserRole
        
        # Get profile
        result = await db.execute(
            select(BusinessProfile).where(BusinessProfile.tenant_id == tenant_id)
        )
        profile = result.scalar_one_or_none()
        
        # If no profile exists for this tenant, securely initialize a default one
        if not profile:
            profile = BusinessProfile(
                tenant_id=tenant_id,
                business_name="",
                app_language="English",
                iot_alerts_enabled=True,
                financial_alerts_enabled=True,
                onboarding_completed=False
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
            
        # Get user (Owner/Admin)
        user_result = await db.execute(
            select(User).where(User.tenant_id == tenant_id, User.role == UserRole.ADMIN)
        )
        user = user_result.scalar_one_or_none()
        
        return ProfileResponse(
            identity={
                "name": user.name if user else "Owner",
                "email": user.email if user else "",
                "avatar_url": user.avatar_url if user else None,
                "role": "Owner"  # We map ADMIN to Owner for the UI
            },
            business={
                "id": profile.id,
                "tenant_id": profile.tenant_id,
                "business_name": profile.business_name,
                "gstin": profile.gstin,
                "contact_number": profile.contact_number,
                "hub_location": profile.hub_location,
                "base_price_today": profile.base_price_today,
                "default_credit_limit": profile.default_credit_limit,
                "iot_alerts_enabled": profile.iot_alerts_enabled,
                "financial_alerts_enabled": profile.financial_alerts_enabled,
                "app_language": profile.app_language,
                "onboarding_completed": profile.onboarding_completed
            }
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Error during get_profile: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.put("", response_model=ProfileResponse)
@router.put("/", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant)
):
    """Update the business profile and identity ensuring cross-tenant boundaries are strictly respected."""
    from models.user import User, UserRole
    
    # 1. Update Business Profile
    if payload.business:
        result = await db.execute(
            select(BusinessProfile).where(BusinessProfile.tenant_id == tenant_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business profile not found for this tenant."
            )
            
        update_data = payload.business.model_dump(exclude_unset=True, exclude={"id", "tenant_id"})
        
        for key, value in update_data.items():
            setattr(profile, key, value)
            
        # Automatically mark onboarding as complete if they saved a business name
        if payload.business.business_name:
            profile.onboarding_completed = True
            
        # Sync contact_number to User table for WhatsApp routing
        if "contact_number" in update_data and update_data["contact_number"]:
            user_result = await db.execute(select(User).where(User.tenant_id == tenant_id, User.role == UserRole.ADMIN))
            user = user_result.scalar_one_or_none()
            if user:
                import re
                clean_phone = re.sub(r'\D', '', update_data["contact_number"])
                if clean_phone and user.phone != clean_phone:
                    other_user_res = await db.execute(select(User).where(User.phone == clean_phone))
                    other_user = other_user_res.scalar_one_or_none()
                    if other_user and other_user.id != user.id:
                        other_user.phone = f"old_{other_user.phone}"
                    user.phone = clean_phone
                    
    # 2. Update Identity
    if payload.identity:
        user_result = await db.execute(
            select(User).where(User.tenant_id == tenant_id, User.role == UserRole.ADMIN)
        )
        user = user_result.scalar_one_or_none()
        if user:
            if payload.identity.name is not None:
                user.name = payload.identity.name

    await db.commit()
    
    # Return updated profile
    return await get_profile(db=db, tenant_id=tenant_id)


@router.post("/upload_avatar", response_model=ProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
):
    """Upload a profile picture to Cloudinary and store the URL on the User."""
    from models.user import User, UserRole
    
    user_result = await db.execute(
        select(User).where(User.tenant_id == tenant_id, User.role == UserRole.ADMIN)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found for this tenant.",
        )

    # Stream to Cloudinary — no local disk I/O
    secure_url = await upload_profile_picture(file, str(tenant_id))

    user.avatar_url = secure_url
    await db.commit()
    
    return await get_profile(db=db, tenant_id=tenant_id)


@router.get("/export")
async def export_data_csv(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant)
):
    """Export Monthly Khata and Order reports as a CSV."""
    
    # Fetch orders for this tenant
    orders_result = await db.execute(
        select(Order).where(Order.tenant_id == tenant_id).order_by(Order.created_at.desc())
    )
    orders = orders_result.scalars().all()
    
    # Fetch khata transactions for this tenant
    khata_result = await db.execute(
        select(KhataTransaction).where(KhataTransaction.tenant_id == tenant_id).order_by(KhataTransaction.created_at.desc())
    )
    khata_txns = khata_result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["--- ORDERS REPORT ---"])
    writer.writerow(["Order ID", "Date", "Status", "Item Type", "Quantity (kg)", "Total Amount", "Source"])
    for o in orders:
        writer.writerow([
            str(o.id),
            o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else "",
            o.status,
            o.item_type,
            o.quantity_kg,
            o.total_amount,
            o.order_source
        ])
        
    writer.writerow([])
    writer.writerow(["--- KHATA REPORT ---"])
    writer.writerow(["Transaction ID", "Date", "Type", "Amount", "Balance After", "Reference Note"])
    for k in khata_txns:
        writer.writerow([
            str(k.id),
            k.created_at.strftime("%Y-%m-%d %H:%M") if k.created_at else "",
            k.type.value if hasattr(k.type, "value") else str(k.type),
            k.amount,
            k.balance_after,
            k.reference_note or ""
        ])
        
    response = Response(content=output.getvalue())
    response.media_type = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=go_chicken_export.csv"
    return response
