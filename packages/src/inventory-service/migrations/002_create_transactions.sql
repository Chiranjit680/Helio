-- Migration: 002_create_transactions
-- Description: Create the inventory_transactions table for tracking stock movements

CREATE TABLE IF NOT EXISTS inventory_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('IN', 'OUT', 'ADJUSTMENT')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    previous_quantity INTEGER NOT NULL,
    new_quantity INTEGER NOT NULL,
    notes TEXT,
    reference_id VARCHAR(100),  -- External reference (PO number, order ID, etc.)
    reference_type VARCHAR(50), -- Type of reference (purchase_order, sales_order, etc.)
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_transactions_item_id ON inventory_transactions(item_id);
CREATE INDEX idx_transactions_type ON inventory_transactions(type);
CREATE INDEX idx_transactions_created_at ON inventory_transactions(created_at);
CREATE INDEX idx_transactions_reference ON inventory_transactions(reference_id, reference_type);

-- Create composite index for item history queries
CREATE INDEX idx_transactions_item_created ON inventory_transactions(item_id, created_at DESC);

-- Add comments
COMMENT ON TABLE inventory_transactions IS 'Tracks all inventory stock movements and adjustments';
COMMENT ON COLUMN inventory_transactions.type IS 'IN = stock received, OUT = stock shipped/consumed, ADJUSTMENT = manual correction';
COMMENT ON COLUMN inventory_transactions.reference_id IS 'External reference like PO number or sales order ID';
