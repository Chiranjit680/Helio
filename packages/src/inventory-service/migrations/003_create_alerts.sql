-- Migration: 003_create_alerts
-- Description: Create the inventory_alerts table for stock alerts and notifications

CREATE TABLE IF NOT EXISTS inventory_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID REFERENCES inventory_items(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('LOW_STOCK', 'CRITICAL_STOCK', 'OUT_OF_STOCK', 'EXPIRING', 'CUSTOM')),
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM' CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH')),
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'ACKNOWLEDGED', 'RESOLVED')),
    threshold INTEGER,           -- Stock threshold that triggered the alert
    current_quantity INTEGER,    -- Quantity at time of alert
    acknowledged_by UUID,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_alerts_item_id ON inventory_alerts(item_id);
CREATE INDEX idx_alerts_type ON inventory_alerts(type);
CREATE INDEX idx_alerts_status ON inventory_alerts(status);
CREATE INDEX idx_alerts_priority ON inventory_alerts(priority);
CREATE INDEX idx_alerts_created_at ON inventory_alerts(created_at);

-- Create index for active alerts (commonly queried)
CREATE INDEX idx_alerts_active ON inventory_alerts(status, priority, created_at DESC) 
    WHERE status = 'ACTIVE';

-- Create index for item's active alerts
CREATE INDEX idx_alerts_item_active ON inventory_alerts(item_id, status) 
    WHERE status = 'ACTIVE';

-- Add trigger to auto-update updated_at
CREATE TRIGGER update_inventory_alerts_updated_at
    BEFORE UPDATE ON inventory_alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments
COMMENT ON TABLE inventory_alerts IS 'Stores inventory alerts for low stock, critical stock, and other notifications';
COMMENT ON COLUMN inventory_alerts.type IS 'Type of alert: LOW_STOCK, CRITICAL_STOCK, OUT_OF_STOCK, EXPIRING, or CUSTOM';
COMMENT ON COLUMN inventory_alerts.status IS 'ACTIVE = needs attention, ACKNOWLEDGED = seen by user, RESOLVED = issue fixed';
