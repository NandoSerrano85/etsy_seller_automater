-- Clear design_images table
-- This will delete all design images but keep the table structure

BEGIN;

-- First, clear the junction table that links designs to templates
DELETE FROM design_template_association;

-- Then clear the design_images table
DELETE FROM design_images;

COMMIT;

-- Verify the tables are empty
SELECT COUNT(*) as design_count FROM design_images;
SELECT COUNT(*) as association_count FROM design_template_association;
