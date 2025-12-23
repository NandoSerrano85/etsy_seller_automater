-- Migration: Add AI tagging columns to design_images table
-- Date: 2025-12-22
-- Description: Adds tags (JSONB array) and tags_metadata (JSONB) columns for AI-powered image tagging

-- Add tags column (JSONB array for storing AI-generated tags)
ALTER TABLE design_images
ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::jsonb;

-- Add tags_metadata column (JSONB for storing tag generation metadata)
ALTER TABLE design_images
ADD COLUMN IF NOT EXISTS tags_metadata JSONB;

-- Create GIN index for efficient tag queries
CREATE INDEX IF NOT EXISTS idx_design_images_tags ON design_images USING gin(tags);

-- Add comments for documentation
COMMENT ON COLUMN design_images.tags IS 'AI-generated tags for searchability (text, objects, style, colors)';
COMMENT ON COLUMN design_images.tags_metadata IS 'Metadata about tag generation (model, processing time, categories, confidence)';
