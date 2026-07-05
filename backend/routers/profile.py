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
    """Fetch the business profile for the currently authenticated tenant."""
    try:
        result = await db.execute(
            select(BusinessProfile).where(BusinessProfile.tenant_id == tenant_id)
        )
        profile = result.scalar_one_or_none()
        
        # If no profile exists for this tenant, securely initialize a default one
        if not profile:
            profile = BusinessProfile(
                tenant_id=tenant_id,
                admin_name="Admin",
                role="Owner",
                business_name="My Business",
                app_language="English",
                iot_alerts_enabled=True,
                financial_alerts_enabled=True
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
            
        return profile
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Database offline during get_profile (%s). Returning demo profile.", e)
        return ProfileResponse(
            tenant_id=tenant_id,
            admin_name="Demo Admin",
            business_name="Demo Business",
            role="Owner",
            contact_number="",
            app_language="English",
            iot_alerts_enabled=True,
            financial_alerts_enabled=True
        )

@router.put("", response_model=ProfileResponse)
@router.put("/", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant)
):
    """Update the business profile ensuring cross-tenant boundaries are strictly respected."""
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.tenant_id == tenant_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found for this tenant."
        )
        
    # Safely apply updates, ignoring None values to support partial updates
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
        
    await db.commit()
    await db.refresh(profile)
    return profile

@router.post("/upload_avatar", response_model=ProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
):
    """Upload a profile picture to Cloudinary and store the URL."""
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.tenant_id == tenant_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found for this tenant.",
        )

    # Stream to Cloudinary — no local disk I/O
    secure_url = await upload_profile_picture(file, str(tenant_id))

    profile.profile_pic_url = secure_url
    await db.commit()
    await db.refresh(profile)
    return profile


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
