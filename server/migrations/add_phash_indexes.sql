-- Migration: Add indexes for perceptual hash duplicate detection
-- Purpose: Optimize duplicate image detection queries
-- Date: 2025-09-30

-- Add indexes for hash columns to enable fast lookups
CREATE INDEX IF NOT EXISTS idx_design_images_phash
ON design_images(phash)
WHERE phash IS NOT NULL AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_design_images_ahash
ON design_images(ahash)
WHERE ahash IS NOT NULL AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_design_images_dhash
ON design_images(dhash)
WHERE dhash IS NOT NULL AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_design_images_whash
ON design_images(whash)
WHERE whash IS NOT NULL AND is_active = true;

-- Composite index for user-specific queries
CREATE INDEX IF NOT EXISTS idx_design_images_user_active
ON design_images(user_id, is_active)
WHERE is_active = true;

-- Add comments for documentation
COMMENT ON INDEX idx_design_images_phash IS 'Perceptual hash index for fast duplicate detection';
COMMENT ON INDEX idx_design_images_ahash IS 'Average hash index for fast duplicate detection';
COMMENT ON INDEX idx_design_images_dhash IS 'Difference hash index for fast duplicate detection';
COMMENT ON INDEX idx_design_images_whash IS 'Wavelet hash index for fast duplicate detection';
COMMENT ON INDEX idx_design_images_user_active IS 'User and active status composite index for filtering';

-- Analyze tables to update statistics
ANALYZE design_images;
