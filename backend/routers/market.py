import uuid
import json
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.auth import get_current_tenant
from models.tenant import Tenant
from core.event_broadcaster import broadcast_event
from models.market import MarketSnapshot, PriceRecommendation
from models.pricing import ProductPrice, PriceBook, PriceBookEntry, PriceHistory
from datetime import timedelta

router = APIRouter(
    prefix="/market",
    tags=["Market Intelligence"],
    responses={401: {"description": "Not authenticated"}},
)

@router.get("/intelligence")
async def get_market_intelligence(
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Fetch the latest MarketSnapshot and any PENDING recommendations."""
    
    # Get latest snapshot for tenant
    stmt = (
        select(MarketSnapshot)
        .where(MarketSnapshot.tenant_id == tenant_id)
        .order_by(MarketSnapshot.captured_at.desc())
        .limit(1)
        .options(selectinload(MarketSnapshot.recommendations))
    )
    result = await db.execute(stmt)
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        return {"snapshot": None, "recommendations": []}

    return {
        "snapshot": {
            "id": str(snapshot.id),
            "captured_at": snapshot.captured_at.isoformat(),
            "source_count": snapshot.source_count,
            "status": snapshot.analysis_status,
            "signals": snapshot.signals,
            "summary": snapshot.summary,
            "confidence": snapshot.confidence
        },
        "recommendations": [
            {
                "id": f"REC-{r.created_at.strftime('%Y%m%d')}-{str(r.id)[:4].upper()}",
                "raw_id": str(r.id),
                "snapshot_id": f"MS-{snapshot.captured_at.strftime('%Y%m%d')}-{str(snapshot.id)[:4].upper()}",
                "sku": r.sku,
                "current_price": float(r.current_price),
                "recommended_price": float(r.recommended_price),
                "confidence_score": r.confidence_score,
                "reasoning": r.reasoning,
                "status": r.status,
                "impact": r.impact,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None
            }
            for r in snapshot.recommendations if r.status == "PENDING"
        ]
    }


@router.post("/recommendations/{recommendation_id}/accept")
async def accept_recommendation(
    recommendation_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Mark recommendation as ACCEPTED and apply the price change."""

    # Fetch recommendation
    stmt = select(PriceRecommendation).where(
        PriceRecommendation.id == recommendation_id,
        PriceRecommendation.tenant_id == tenant_id,
        PriceRecommendation.status == "PENDING"
    )
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()

    if not rec:
        raise HTTPException(status_code=404, detail="Pending recommendation not found")

    # 1. Update the recommendation status
    rec.status = "ACCEPTED"
    rec.updated_at = datetime.now(timezone.utc)

    # 2. Update the ProductPrice (Legacy model but we keep it in sync for the dashboard)
    stmt_prod = select(ProductPrice).where(ProductPrice.item_type == rec.sku)
    result_prod = await db.execute(stmt_prod)
    prod_price = result_prod.scalar_one_or_none()

    old_price = None
    if prod_price:
        old_price = prod_price.price_per_kg
        prod_price.price_per_kg = rec.recommended_price
        prod_price.updated_at = datetime.now(timezone.utc)
    else:
        # Create it if it doesn't exist
        prod_price = ProductPrice(
            item_type=rec.sku,
            price_per_kg=rec.recommended_price
        )
        db.add(prod_price)

    # 3. Update the Base Tier PriceBook (Enterprise model)
    stmt_pb = select(PriceBook).where(
        PriceBook.tenant_id == tenant_id,
        PriceBook.name == "Base Wholesale"
    )
    result_pb = await db.execute(stmt_pb)
    pb = result_pb.scalar_one_or_none()
    
    if pb:
        stmt_pbe = select(PriceBookEntry).where(
            PriceBookEntry.price_book_id == pb.id,
            PriceBookEntry.sku == rec.sku
        )
        result_pbe = await db.execute(stmt_pbe)
        pbe = result_pbe.scalar_one_or_none()
        
        if pbe:
            if not old_price:
                old_price = pbe.base_unit_price
            pbe.base_unit_price = rec.recommended_price
            pbe.updated_at = datetime.now(timezone.utc)
            
            # Log audit
            history = PriceHistory(
                tenant_id=tenant_id,
                entity_type="PRICE_BOOK_ENTRY",
                entity_id=pbe.id,
                old_price=old_price,
                new_price=rec.recommended_price
            )
            db.add(history)

    await db.commit()

    # Emit standard WebSocket system event
    await broadcast_event(
        "pricing.recommendation.accepted",
        {
            "tenant_id": str(tenant_id),
            "sku": rec.sku,
            "new_price": float(rec.recommended_price),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    return {"message": "Accepted", "new_price": float(rec.recommended_price)}


@router.post("/recommendations/{recommendation_id}/ignore")
async def ignore_recommendation(
    recommendation_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Mark recommendation as IGNORED."""

    stmt = select(PriceRecommendation).where(
        PriceRecommendation.id == recommendation_id,
        PriceRecommendation.tenant_id == tenant_id,
        PriceRecommendation.status == "PENDING"
    )
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()

    if not rec:
        raise HTTPException(status_code=404, detail="Pending recommendation not found")

    rec.status = "IGNORED"
    rec.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Ignored"}


@router.post("/simulations/{scenario}")
async def simulate_market(
    scenario: str,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Trigger an AI Market Intelligence simulation."""
    
    now_utc = datetime.now(timezone.utc)
    expires = now_utc + timedelta(minutes=30)

    # 1. Supersede any currently pending recommendations
    await db.execute(
        PriceRecommendation.__table__.update()
        .where(PriceRecommendation.tenant_id == tenant_id)
        .where(PriceRecommendation.status == "PENDING")
        .values(status="SUPERSEDED", updated_at=now_utc)
    )

    # Determine current price for BROILER
    stmt_prod = select(ProductPrice).where(ProductPrice.item_type == "BROILER")
    result_prod = await db.execute(stmt_prod)
    prod_price = result_prod.scalar_one_or_none()
    current_broiler_price = prod_price.price_per_kg if prod_price else Decimal("220.00")

    if scenario == "weekend-demand":
        snapshot = MarketSnapshot(
            tenant_id=tenant_id,
            source_count=8,
            captured_at=now_utc,
            analysis_status="COMPLETED",
            signals=[
                {"source": "Supplier Trends", "signal": "Weekend Demand", "weight": "+42%"},
                {"source": "Wholesale Board", "signal": "Supplier Increase", "weight": "+35%"},
                {"source": "Warehouse", "signal": "Inventory Pressure", "weight": "+15%"},
                {"source": "Agri Index", "signal": "Feed Cost", "weight": "+8%"}
            ],
            summary="Weekend demand increasing across monitored suppliers.",
            confidence=94
        )
        db.add(snapshot)
        await db.flush()

        rec = PriceRecommendation(
            tenant_id=tenant_id,
            snapshot_id=snapshot.id,
            sku="BROILER",
            current_price=current_broiler_price,
            recommended_price=current_broiler_price + Decimal("5.00"),
            confidence_score=96,
            reasoning=[
                "Supplier A increased broiler rates",
                "Historical weekend demand trend",
                "Feed costs remained stable"
            ],
            impact={
                "expected_daily_revenue": "+₹12,400",
                "estimated_margin": "+2.3%",
                "affected_retailers": 126
            },
            status="PENDING",
            expires_at=expires,
            created_at=now_utc,
            updated_at=now_utc
        )
        db.add(rec)
    elif scenario == "feed-cost-spike":
        snapshot = MarketSnapshot(
            tenant_id=tenant_id,
            source_count=10,
            captured_at=now_utc,
            analysis_status="COMPLETED",
            signals=[
                {"source": "Agri Index", "signal": "Maize prices", "weight": "+55%"},
                {"source": "Transport", "signal": "Diesel prices", "weight": "+25%"},
                {"source": "Wholesale Board", "signal": "Supply constraint", "weight": "+20%"}
            ],
            summary="Supply constraints and feed cost spikes detected.",
            confidence=88
        )
        db.add(snapshot)
        await db.flush()

        rec = PriceRecommendation(
            tenant_id=tenant_id,
            snapshot_id=snapshot.id,
            sku="BROILER",
            current_price=current_broiler_price,
            recommended_price=current_broiler_price + Decimal("8.00"),
            confidence_score=88,
            reasoning=[
                "Maize feed costs surged by 8%",
                "Local transport costs increased",
                "Supply constraint warnings issued"
            ],
            impact={
                "expected_daily_revenue": "+₹6,800",
                "estimated_margin": "-0.5%",
                "affected_retailers": 142
            },
            status="PENDING",
            expires_at=expires,
            created_at=now_utc,
            updated_at=now_utc
        )
        db.add(rec)
    elif scenario == "no-action":
        snapshot = MarketSnapshot(
            tenant_id=tenant_id,
            source_count=8,
            captured_at=now_utc,
            analysis_status="COMPLETED",
            signals=[
                {"source": "Supplier Trends", "signal": "Demand Stable", "weight": "0%"},
                {"source": "Wholesale Board", "signal": "Prices Unchanged", "weight": "0%"},
                {"source": "Agri Index", "signal": "Feed Stable", "weight": "0%"}
            ],
            summary="Market conditions are stable across all monitored sources.",
            confidence=97
        )
        db.add(snapshot)
        await db.flush()

        rec = PriceRecommendation(
            tenant_id=tenant_id,
            snapshot_id=snapshot.id,
            sku="BROILER",
            current_price=current_broiler_price,
            recommended_price=current_broiler_price,
            confidence_score=97,
            reasoning=[
                "No pricing changes recommended."
            ],
            impact=None,
            status="PENDING",
            expires_at=expires,
            created_at=now_utc,
            updated_at=now_utc
        )
        db.add(rec)
    elif scenario == "clear":
        # Delete all snapshots and recommendations
        await db.execute(MarketSnapshot.__table__.delete().where(MarketSnapshot.tenant_id == tenant_id))
        await db.execute(PriceRecommendation.__table__.delete().where(PriceRecommendation.tenant_id == tenant_id))
        await db.commit()
        return {"message": "Market Intelligence reset"}
    else:
        raise HTTPException(status_code=400, detail="Unknown scenario")

    await db.commit()
    return {"message": f"Simulation {scenario} executed successfully."}
