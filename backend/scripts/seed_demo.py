"""Enterprise Demo Data Seeding Script — Go Chicken Hackathon Pivot.

Populates the PostgreSQL database with a rich, relational, highly realistic business state:
- 1 Tenant + BusinessProfile ("Jagan Supplies", Super Admin "Jagan Mohan")
- 1 Admin User, 3 Drivers, 5 Retailers (Raju Chicken Center, Bhavani Poultry, Kalyan Meats, Durga Broilers, Lakshmi Broilers)
- 4 Trucks with IoT temperature readings and alerts
- Price books, price entries, and quotes
- Inventory items and detailed transactions
- 100+ Orders across the last 14 days with full timeline history
- Khata ledger entries, customer balance projections, and invoices
- Analytics daily KPIs and AI forecasts for immediate chart rendering

Usage:
    python -m scripts.seed_demo
    OR
    python scripts/seed_demo.py
"""

import asyncio
import logging
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

# Ensure project root is on sys.path when running script directly
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import get_settings
from models.base import Base
from models.tenant import Tenant
from models.profile import BusinessProfile
from models.user import User, UserRole
from models.logistics import Truck, IoTReading
from models.pricing import (
    ProductPrice,
    PriceBook,
    PriceBookEntry,
    CustomerPriceOverride,
    Quote,
    QuoteItem,
)
from models.inventory import InventoryItem, InventoryTransaction
from models.khata import (
    KhataTransaction,
    TransactionType,
    KhataLedger,
    CustomerBalanceProjection,
    KhataInvoice,
)
from models.order import Order
from models.order_timeline import OrderTimeline
from models.ai import AIForecast
from models.analytics import (
    OperationalDailyKPI,
    FinancialDailyKPI,
    CommunicationDailyKPI,
    ProjectionMetadata,
    AnalyticsEventProcessed,
)
from models.classification_log import ClassificationLog
from models.communication import CommunicationLog
from models.error_log import ErrorLog

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("go_chicken.seed_demo")


async def clear_database(db: AsyncSession):
    """Safely clear existing data in reverse foreign-key dependency order."""
    logger.info("Clearing existing data from database tables...")
    tables = [
        OrderTimeline,
        IoTReading,
        QuoteItem,
        Quote,
        KhataInvoice,
        CustomerBalanceProjection,
        KhataLedger,
        KhataTransaction,
        InventoryTransaction,
        InventoryItem,
        Order,
        Truck,
        CustomerPriceOverride,
        PriceBookEntry,
        PriceBook,
        ProductPrice,
        AIForecast,
        OperationalDailyKPI,
        FinancialDailyKPI,
        CommunicationDailyKPI,
        ProjectionMetadata,
        AnalyticsEventProcessed,
        CommunicationLog,
        ClassificationLog,
        ErrorLog,
        BusinessProfile,
        User,
        Tenant,
    ]
    for table in tables:
        await db.execute(delete(table))
    await db.commit()
    logger.info("Database tables cleared successfully.")


async def seed_demo_data(db: AsyncSession):
    """Seed comprehensive, consistent business state."""
    logger.info("Starting relational demo data seeding...")
    now_utc = datetime.now(timezone.utc)
    today = date.today()

    # ─────────────────────────────────────────────────────────────────────────────
    # 1. Tenant & Business Profile
    # ─────────────────────────────────────────────────────────────────────────────
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Go Chicken Tenant",
        created_at=now_utc - timedelta(days=30),
    )
    db.add(tenant)

    profile = BusinessProfile(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        admin_name="Jagan Mohan",
        role="Super Admin",
        business_name="Jagan Supplies",
        gstin="37AAACJ1234A1Z5",
        contact_number="+91 98765 43210",
        hub_location="Vijayawada Hub",
        base_price_today=Decimal("135.00"),
        default_credit_limit=Decimal("100000.00"),
        iot_alerts_enabled=True,
        financial_alerts_enabled=True,
        app_language="English",
    )
    db.add(profile)

    # ─────────────────────────────────────────────────────────────────────────────
    # 2. Users: Admin, Drivers, and Retailers
    # ─────────────────────────────────────────────────────────────────────────────
    admin_user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        role=UserRole.ADMIN,
        name="Jagan Mohan",
        phone="919876543210",
        email="admin@jagansupplies.com",
        created_at=now_utc - timedelta(days=30),
    )
    db.add(admin_user)

    # 3 Drivers
    driver_data = [
        ("Suresh Kumar", "919811111111"),
        ("Ramesh Babu", "919822222222"),
        ("Venkat Rao", "919833333333"),
    ]
    drivers = []
    for d_name, d_phone in driver_data:
        driver = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            role=UserRole.DRIVER,
            name=d_name,
            phone=d_phone,
            email=f"{d_name.lower().replace(' ', '')}@jagansupplies.com",
            created_at=now_utc - timedelta(days=25),
        )
        db.add(driver)
        drivers.append(driver)

    # 5 Retailers
    retailer_data = [
        ("Raju Chicken Center", "919876543211", "MG Road, Patamata, Vijayawada", Decimal("16.5062"), Decimal("80.6480")),
        ("Bhavani Poultry", "919876543212", "Governor Peta, Vijayawada", Decimal("16.5131"), Decimal("80.6218")),
        ("Kalyan Meats", "919876543213", "Benz Circle, Vijayawada", Decimal("16.5020"), Decimal("80.6540")),
        ("Durga Broilers", "919876543214", "Bhavanipuram, Vijayawada", Decimal("16.5200"), Decimal("80.5900")),
        ("Lakshmi Broilers", "919876543215", "Satyanarayanapuram, Vijayawada", Decimal("16.5180"), Decimal("80.6350")),
    ]
    retailers = []
    for r_name, r_phone, r_addr, r_lat, r_lng in retailer_data:
        retailer = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            role=UserRole.RETAILER,
            name=r_name,
            phone=r_phone,
            email=f"{r_name.lower().replace(' ', '')}@gmail.com",
            shop_address=r_addr,
            latitude=r_lat,
            longitude=r_lng,
            created_at=now_utc - timedelta(days=25),
        )
        db.add(retailer)
        retailers.append(retailer)

    # ─────────────────────────────────────────────────────────────────────────────
    # 3. Trucks & IoT Readings
    # ─────────────────────────────────────────────────────────────────────────────
    truck_data = [
        ("AP 16 TZ 1001", "IOT-TRK-101", Decimal("1500.00"), drivers[0].id),
        ("AP 16 TZ 1002", "IOT-TRK-102", Decimal("1200.00"), drivers[1].id),
        ("AP 16 TZ 1003", "IOT-TRK-103", Decimal("1000.00"), drivers[2].id),
        ("AP 16 TZ 1004", "IOT-TRK-104", Decimal("2000.00"), None),
    ]
    trucks = []
    for t_plate, t_iot, t_cap, t_driver_id in truck_data:
        truck = Truck(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            driver_id=t_driver_id,
            license_plate=t_plate,
            iot_device_id=t_iot,
            max_capacity_kg=t_cap,
            created_at=now_utc - timedelta(days=20),
        )
        db.add(truck)
        trucks.append(truck)

    # IoT readings
    iot_readings_info = [
        (trucks[0].id, Decimal("-1.20"), False),
        (trucks[0].id, Decimal("-1.00"), False),
        (trucks[1].id, Decimal("30.50"), True),  # Alert triggered!
        (trucks[2].id, Decimal("2.40"), False),
        (trucks[3].id, Decimal("-0.80"), False),
    ]
    for t_id, temp, alert in iot_readings_info:
        reading = IoTReading(
            id=uuid.uuid4(),
            truck_id=t_id,
            temperature=temp,
            recorded_at=now_utc - timedelta(minutes=15),
            alert_triggered=alert,
        )
        db.add(reading)

    # ─────────────────────────────────────────────────────────────────────────────
    # 4. Pricing & Quotes
    # ─────────────────────────────────────────────────────────────────────────────
    skus = [
        ("Live Bird", Decimal("135.00")),
        ("Broiler", Decimal("155.00")),
        ("DESI", Decimal("210.00")),
        ("Country Chicken", Decimal("265.00")),
    ]
    for sku_name, price in skus:
        pp = ProductPrice(
            id=uuid.uuid4(),
            item_type=sku_name,
            price_per_kg=price,
            updated_at=now_utc,
        )
        db.add(pp)

    price_book = PriceBook(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Wholesale Tier 1",
        is_active=True,
        effective_date=today - timedelta(days=30),
        created_at=now_utc - timedelta(days=30),
        updated_at=now_utc,
    )
    db.add(price_book)

    for sku_name, price in skus:
        pbe = PriceBookEntry(
            id=uuid.uuid4(),
            price_book_id=price_book.id,
            sku=sku_name,
            base_unit_price=price,
            min_quantity_kg=Decimal("10.00"),
            created_at=now_utc - timedelta(days=30),
            updated_at=now_utc,
        )
        db.add(pbe)

    # Sample Quote for Raju Chicken Center
    quote = Quote(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        quote_number="QT-2026-001",
        quote_version=1,
        customer_id=retailers[0].id,
        delivery_zone="Patamata",
        status="APPROVED",
        subtotal_amount=Decimal("13500.00"),
        zone_surcharge_amount=Decimal("200.00"),
        total_amount=Decimal("13700.00"),
        expires_at=now_utc + timedelta(days=7),
        created_at=now_utc - timedelta(hours=3),
        updated_at=now_utc - timedelta(hours=3),
    )
    db.add(quote)

    quote_item = QuoteItem(
        id=uuid.uuid4(),
        quote_id=quote.id,
        sku="Live Bird",
        quantity_kg=Decimal("100.00"),
        unit_price=Decimal("135.00"),
        pricing_source="TIER_PRICEBOOK",
        line_total=Decimal("13500.00"),
    )
    db.add(quote_item)

    # ─────────────────────────────────────────────────────────────────────────────
    # 5. Inventory & Transactions
    # ─────────────────────────────────────────────────────────────────────────────
    inv_data = [
        ("Live Bird", Decimal("4500.00"), Decimal("600.00"), Decimal("800.00"), Decimal("3100.00"), Decimal("500.00"), Decimal("800.00")),
        ("Broiler", Decimal("3200.00"), Decimal("400.00"), Decimal("500.00"), Decimal("2300.00"), Decimal("400.00"), Decimal("600.00")),
        ("DESI", Decimal("1200.00"), Decimal("150.00"), Decimal("200.00"), Decimal("850.00"), Decimal("200.00"), Decimal("350.00")),
        ("Country Chicken", Decimal("800.00"), Decimal("100.00"), Decimal("100.00"), Decimal("600.00"), Decimal("150.00"), Decimal("250.00")),
    ]
    inv_items = {}
    for item_type, avail, res, loaded, deliv, min_s, reorder in inv_data:
        inv = InventoryItem(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            item_type=item_type,
            unit="KG",
            available_qty=avail,
            reserved_qty=res,
            loaded_qty=loaded,
            delivered_qty=deliv,
            waste_qty=Decimal("15.00"),
            returned_qty=Decimal("0.00"),
            minimum_stock=min_s,
            reorder_level=reorder,
            created_at=now_utc - timedelta(days=20),
            updated_at=now_utc,
        )
        db.add(inv)
        inv_items[item_type] = inv

        # Inventory transaction history
        tx = InventoryTransaction(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            inventory_item_id=inv.id,
            transaction_type="STOCK_IN",
            quantity=avail + res + loaded + deliv,
            reference_type="PURCHASE_ORDER",
            reference_id="PO-DAILY-INBOUND",
            remarks="Daily stock replenishment from farm",
            performed_by="Jagan Mohan",
            created_at=now_utc - timedelta(hours=8),
        )
        db.add(tx)

    # ─────────────────────────────────────────────────────────────────────────────
    # 6. Orders across 14 days (120 orders)
    # ─────────────────────────────────────────────────────────────────────────────
    statuses = ["delivered", "delivered", "delivered", "out_for_delivery", "loaded", "confirmed", "pending"]
    item_types = ["Live Bird", "Broiler", "DESI", "Country Chicken"]
    prices_map = {"Live Bird": Decimal("135.00"), "Broiler": Decimal("155.00"), "DESI": Decimal("210.00"), "Country Chicken": Decimal("265.00")}

    orders = []
    for i in range(120):
        days_ago = (i % 14)
        order_time = now_utc - timedelta(days=days_ago, hours=(i % 12), minutes=(i * 13) % 60)
        retailer = retailers[i % len(retailers)]
        truck = trucks[i % len(trucks)] if i % 4 != 3 else None
        item_type = item_types[i % len(item_types)]
        unit_price = prices_map[item_type]
        quantity = Decimal(str(50 + ((i * 35) % 350)))
        total_amt = quantity * unit_price
        
        # Determine status: older orders are delivered, today/yesterday span active statuses
        if days_ago > 1:
            status = "delivered"
        else:
            status = statuses[i % len(statuses)]

        order = Order(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            retailer_id=retailer.id,
            truck_id=truck.id if truck else None,
            phone_number=retailer.phone,
            item_type=item_type,
            quantity_kg=quantity,
            price_per_kg=unit_price,
            unit_price=unit_price,
            total_amount=total_amt,
            status=status,
            order_source="ollama" if i % 5 != 0 else "regex",
            delivery_date=order_time + timedelta(hours=6),
            driver_phone=truck.driver.phone if (truck and truck.driver) else None,
            driver_name=truck.driver.name if (truck and truck.driver) else None,
            dispatch_time=order_time + timedelta(hours=2) if status in ("loaded", "out_for_delivery", "delivered") else None,
            created_at=order_time,
            updated_at=order_time + timedelta(hours=4),
        )
        db.add(order)
        orders.append(order)

        # Order Timeline entry
        timeline = OrderTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            order_id=order.id,
            from_status="pending" if status != "pending" else None,
            to_status=status,
            performed_by="System / Driver App",
            reason=f"Order status updated to {status}",
            created_at=order_time + timedelta(minutes=30),
        )
        db.add(timeline)

    # ─────────────────────────────────────────────────────────────────────────────
    # 7. Khata Ledger & Projections
    # ─────────────────────────────────────────────────────────────────────────────
    balances_map = {
        retailers[0].id: Decimal("8200.00"),
        retailers[1].id: Decimal("14500.00"),
        retailers[2].id: Decimal("-1200.00"), # Advance credit
        retailers[3].id: Decimal("4500.00"),
        retailers[4].id: Decimal("0.00"),
    }

    for idx, retailer in enumerate(retailers):
        bal = balances_map[retailer.id]
        
        # Customer balance projection
        proj = CustomerBalanceProjection(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            customer_id=retailer.id,
            outstanding_balance=bal,
            last_entry_at=now_utc,
            updated_at=now_utc,
        )
        db.add(proj)

        # Legacy Khata Transaction
        kt = KhataTransaction(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            retailer_id=retailer.id,
            order_id=orders[idx].id,
            type=TransactionType.CHARGE if bal >= 0 else TransactionType.PAYMENT,
            amount=abs(bal) if bal != 0 else Decimal("5000.00"),
            balance_after=bal,
            reference_note=f"Ledger reconciliation for {retailer.name}",
            created_at=now_utc - timedelta(days=1),
        )
        db.add(kt)

        # Enterprise Khata Ledger
        kl = KhataLedger(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            customer_id=retailer.id,
            entry_type="INVOICE" if bal >= 0 else "PAYMENT",
            amount=bal if bal != 0 else Decimal("5000.00"),
            reference_type="ORDER",
            reference_id=str(orders[idx].id),
            idempotency_key=f"IDEM-SEED-{retailer.id}-{idx}",
            notes=f"Initial seed entry for {retailer.name}",
            created_at=now_utc - timedelta(days=1),
        )
        db.add(kl)

        # Khata Invoice
        inv_record = KhataInvoice(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            customer_id=retailer.id,
            invoice_id=orders[idx].id,
            total_amount=Decimal("15000.00"),
            settled_amount=Decimal("15000.00") - bal if bal > 0 else Decimal("15000.00"),
            status="PARTIALLY_PAID" if bal > 0 else "PAID",
            issued_at=now_utc - timedelta(days=2),
        )
        db.add(inv_record)

    # ─────────────────────────────────────────────────────────────────────────────
    # 8. Analytics Projections & AI Forecasts
    # ─────────────────────────────────────────────────────────────────────────────
    for i in range(14):
        kpi_date = today - timedelta(days=i)
        
        op_kpi = OperationalDailyKPI(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            metric_date=kpi_date,
            projection_version="v1",
            total_orders_placed=15 + (i % 5),
            orders_confirmed=14 + (i % 5),
            orders_delivered=13 + (i % 5),
            total_volume_kg=Decimal(str(1800 + (i * 120))),
            created_at=now_utc - timedelta(days=i),
            updated_at=now_utc - timedelta(days=i),
        )
        db.add(op_kpi)

        fin_kpi = FinancialDailyKPI(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            metric_date=kpi_date,
            projection_version="v1",
            invoices_issued_total=Decimal(str(245000 + (i * 15000))),
            payments_collected_total=Decimal(str(230000 + (i * 14000))),
            outstanding_receivable_net=Decimal("26000.00"),
            created_at=now_utc - timedelta(days=i),
            updated_at=now_utc - timedelta(days=i),
        )
        db.add(fin_kpi)

        comm_kpi = CommunicationDailyKPI(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            metric_date=kpi_date,
            projection_version="v1",
            messages_dispatched=45 + (i * 3),
            messages_delivered=44 + (i * 3),
            messages_failed=1 if i % 3 == 0 else 0,
            created_at=now_utc - timedelta(days=i),
            updated_at=now_utc - timedelta(days=i),
        )
        db.add(comm_kpi)

        # AI Forecasts
        forecast = AIForecast(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            target_date=kpi_date,
            weather_condition="Sunny, 34°C" if i % 2 == 0 else "Cloudy, 29°C",
            predicted_demand_kg=Decimal(str(2000 + (i * 100))),
            actual_demand_kg=Decimal(str(1950 + (i * 110))) if i > 0 else None,
            historical_context="Festival season impact factored into demand model.",
            created_at=now_utc - timedelta(days=i),
        )
        db.add(forecast)

    # Projection Metadata tracker
    meta = ProjectionMetadata(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        projection_name="operational_daily_kpi",
        projection_version="v1",
        last_processed_at=now_utc,
        rebuild_completed_at=now_utc,
    )
    db.add(meta)

    await db.commit()
    logger.info("✅ Relational demo seeding completed successfully! Database is primed and ready.")


async def main():
    """Entrypoint for standalone script execution."""
    settings = get_settings()
    db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
    logger.info(f"Connecting to database at {db_url.split('@')[-1]}...")
    engine = create_async_engine(db_url, echo=False)

    # Create all schema tables if they do not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as db:
        await clear_database(db)
        await seed_demo_data(db)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
