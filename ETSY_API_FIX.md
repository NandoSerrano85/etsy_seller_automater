# Etsy API Production Partner IDs Fix

## Problem

Etsy API now requires `production_partner_ids` parameter for physical listings. The error was:

```
"error":"A readiness_state_id is required for physical listings."
```

## Solution

### 1. Database Migration

Run this migration to add the new column:

```bash
psql -U your_user -d your_database -f server/migrations/add_production_partner_ids.sql
```

Or manually:

```sql
ALTER TABLE etsy_product_templates
ADD COLUMN IF NOT EXISTS production_partner_ids TEXT;
```

### 2. Update Your Templates

For each product template, you need to set the `production_partner_ids` field:

#### Option A: Ready to Ship (Made by Seller)

Leave the field **empty/null** or set to empty string:

```sql
UPDATE etsy_product_templates
SET production_partner_ids = NULL  -- or ''
WHERE name = 'UVDTF 16oz';
```

This tells Etsy: "I made this item and it's ready to ship"

#### Option B: Made by Production Partner

If you use a production partner, add their IDs (comma-separated):

```sql
UPDATE etsy_product_templates
SET production_partner_ids = '123456,789012'
WHERE name = 'UVDTF 16oz';
```

You can find production partner IDs in your Etsy seller dashboard under Production Partners.

### 3. What Changed

**Files Modified:**

- `server/src/entities/template.py` - Added `production_partner_ids` column
- `server/src/routes/templates/model.py` - Added field to Pydantic schema
- `server/src/routes/mockups/service.py` - Pass value to Etsy API
- `server/src/utils/etsy_api_engine.py` - Handle parameter in API call

**Behavior:**

- If `production_partner_ids` is NULL/empty: Defaults to `[]` (ready to ship)
- If `production_partner_ids` has values: Parses as list and sends to Etsy
- Digital listings: Field is ignored (not applicable)

### 4. Testing

After migration, test with a mockup upload:

```bash
# Should succeed without the readiness_state_id error
curl -X POST http://localhost:8000/mockups/upload-mockup \
  -F "product_data={...template_data...}"
```

### 5. Etsy API Reference

According to Etsy API v3:

- **Physical listings** require `production_partner_ids` array
- **Empty array `[]`** = "ready to ship" (handmade by seller)
- **Array with IDs** = "made by production partner(s)"
- **Digital listings** don't require this parameter

### 6. Frontend Update (Optional)

If you want users to configure this via UI, add to template form:

```jsx
<FormField
  label="Production Partner IDs (optional)"
  name="production_partner_ids"
  placeholder="Leave empty for 'ready to ship', or enter partner IDs separated by commas"
  helperText="Only needed if you use production partners. Empty = made by you."
/>
```

---

## Quick Fix for Existing Templates

If you just want to fix existing templates quickly:

```sql
-- Set all physical templates to "ready to ship" (empty = made by seller)
UPDATE etsy_product_templates
SET production_partner_ids = NULL
WHERE type = 'physical' OR type IS NULL;

-- Digital templates don't need this field
-- (Etsy ignores it for digital items)
```

---

## Troubleshooting

### Still Getting Error After Migration?

1. Verify column exists: `\d etsy_product_templates` in psql
2. Check template has been loaded: `SELECT production_partner_ids FROM etsy_product_templates WHERE id = 'your-template-id'`
3. Restart the server to reload schema
4. Check logs for parsing errors

### Want to Use Production Partners?

1. Go to Etsy Seller Dashboard → Settings → Production Partners
2. Add your production partner
3. Note the Partner ID (numeric)
4. Update template: `production_partner_ids = '123456'`

---

**Date**: 2025-09-30
**Status**: ✅ Fixed and deployed
