-- Migration: Add production_partner_ids column to etsy_product_templates
-- Purpose: Support Etsy API requirement for physical listings
-- Date: 2025-09-30

-- Add production_partner_ids column
ALTER TABLE etsy_product_templates
ADD COLUMN IF NOT EXISTS production_partner_ids TEXT;

-- Add comment for documentation
COMMENT ON COLUMN etsy_product_templates.production_partner_ids IS 'Comma-separated list of production partner IDs. Empty/null means "ready to ship" (made by seller). Required for physical items in Etsy API.';

-- Analyze table to update statistics
ANALYZE etsy_product_templates;
