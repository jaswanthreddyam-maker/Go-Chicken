-- 1. Tenants (Wholesalers)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users (Wholesaler Admins, Drivers, Retailers)
CREATE TYPE user_role AS ENUM ('admin', 'driver', 'retailer');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    role user_role NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    whatsapp_id VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255), -- Keep for Admins/Wholesalers only
    
    -- New Fields for Retailer Routing
    shop_address TEXT,
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_tenant_role ON users(tenant_id, role);

-- 3. Trucks & IoT Devices
CREATE TABLE trucks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    driver_id UUID REFERENCES users(id) ON DELETE SET NULL,
    license_plate VARCHAR(50) NOT NULL,
    iot_device_id VARCHAR(100) UNIQUE,
    
    -- New Field for Dispatch Logic
    max_capacity_kg NUMERIC(10,2) NOT NULL DEFAULT 1000.00,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_trucks_tenant ON trucks(tenant_id);

-- 4. IoT Temperature Logs (Time-Series)
CREATE TABLE iot_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    truck_id UUID REFERENCES trucks(id) ON DELETE CASCADE,
    temperature NUMERIC(5,2) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    alert_triggered BOOLEAN DEFAULT FALSE -- Flagged if temp > safe threshold
);
CREATE INDEX idx_iot_truck_time ON iot_readings(truck_id, recorded_at DESC);

-- 5. Inventory (Stock & Mortality Tracking)
CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    bird_type VARCHAR(100),
    quantity_kg NUMERIC(10,2) NOT NULL DEFAULT 0,
    mortality_kg NUMERIC(10,2) NOT NULL DEFAULT 0, -- Dead stock tracking
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_inventory_tenant ON inventory(tenant_id);

-- 6. Orders
CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'in_transit', 'delivered', 'cancelled');

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    retailer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phone_number VARCHAR(20),
    truck_id UUID REFERENCES trucks(id) ON DELETE SET NULL,
    status order_status DEFAULT 'pending',
    
    -- New Field to differentiate stock
    item_type VARCHAR(50) DEFAULT 'Live Bird', 
    
    quantity_kg NUMERIC(10,2) NOT NULL,
    price_per_kg NUMERIC(10,2) NOT NULL,
    total_amount NUMERIC(12,2) NOT NULL,
    order_source VARCHAR(20) DEFAULT 'regex',  -- 'ollama' or 'regex' — tracks classification method
    delivery_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_orders_tenant ON orders(tenant_id);
CREATE INDEX idx_orders_retailer_date ON orders(retailer_id, delivery_date DESC);

-- 7. Khata (Digital Ledger for Retailers)
CREATE TYPE transaction_type AS ENUM ('charge', 'payment', 'adjustment');

CREATE TABLE khata_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    retailer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL, -- Null for standalone payments
    type transaction_type NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    balance_after NUMERIC(12,2) NOT NULL, -- Running balance for performance
    reference_note TEXT, -- e.g., "UPI Payment", "Mortality Adjustment"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_khata_tenant ON khata_transactions(tenant_id);
CREATE INDEX idx_khata_retailer ON khata_transactions(retailer_id, created_at DESC);

-- 8. AI Vectors & Forecasting Context
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE ai_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    target_date DATE NOT NULL,
    weather_condition VARCHAR(100),
    predicted_demand_kg NUMERIC(10,2),
    actual_demand_kg NUMERIC(10,2),
    historical_context TEXT, 
    
    -- Adjusted dimension for nomic-embed-text (Ollama)
    embedding VECTOR(768), 
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_ai_forecasts_tenant_date ON ai_forecasts(tenant_id, target_date);
CREATE INDEX idx_ai_forecasts_embedding ON ai_forecasts USING hnsw (embedding vector_l2_ops);

-- 9. Error Logs (Background Task Failures)
CREATE TABLE error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(100) NOT NULL,       -- e.g., "whatsapp_webhook", "ollama_classify"
    error_type VARCHAR(255) NOT NULL,   -- Exception class name
    error_message TEXT NOT NULL,         -- Full error message
    stack_trace TEXT,                    -- Full traceback for debugging
    payload JSONB,                      -- The raw payload that caused the error
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_error_logs_source ON error_logs(source, created_at DESC);

-- 10. Classification Logs (Ollama/Regex Monitoring — Brain Health Dashboard)
CREATE TABLE classification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_snippet TEXT NOT NULL,           -- First 100 chars of the WhatsApp message
    intent VARCHAR(20),                      -- ORDER, INQUIRY, GREETING, or NULL if Ollama failed
    confidence FLOAT DEFAULT 0.0,            -- Ollama's confidence score (0.0 if failed/regex)
    order_source VARCHAR(20) NOT NULL,       -- 'ollama' or 'regex' — which classifier was used
    latency_ms INT DEFAULT 0,               -- Ollama response time in milliseconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_classification_logs_source ON classification_logs(order_source, created_at DESC);
CREATE INDEX idx_classification_logs_confidence ON classification_logs(confidence);
CREATE INDEX idx_classification_logs_intent ON classification_logs(intent, created_at DESC);

-- -----------------------------------------------------------------------------
-- 8. PRODUCT PRICES (Dynamic Pricing Control for Dashboard & WhatsApp Bot)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_prices (
    item_type VARCHAR(50) PRIMARY KEY,       -- 'Live Bird', 'Dressed', 'Skinless'
    price_per_kg NUMERIC(10, 2) NOT NULL,    -- Current price per kg in INR
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
