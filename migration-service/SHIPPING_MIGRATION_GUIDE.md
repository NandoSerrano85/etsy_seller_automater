# Shipping & Handling Fee Migration Guide

This guide covers all migrations related to the shipping and handling fee features.

## Overview

The shipping system includes:

1. **Shippo API Integration** - Real-time shipping rates from USPS, UPS, FedEx
2. **Handling Fee** - Configurable fee added to all shipping costs
3. **Database Storage** - Origin address, package dimensions, API keys stored in DB
4. **Multi-carrier Support** - USPS, UPS, FedEx rates with fallback options

## Migrations Included

### 1. `add_shipping_config_to_storefront_settings.py`

**What it does:** Adds shipping configuration columns to storefront settings table

**Columns added:**

- `shipping_from_name` - Business name for shipping label
- `shipping_from_company` - Company name
- `shipping_from_street1` - Origin street address
- `shipping_from_street2` - Apartment/Suite (optional)
- `shipping_from_city` - Origin city
- `shipping_from_state` - Origin state
- `shipping_from_zip` - Origin ZIP code
- `shipping_from_country` - Origin country (default: US)
- `shipping_from_phone` - Contact phone
- `shipping_from_email` - Contact email
- `shipping_default_length` - Default package length (inches)
- `shipping_default_width` - Default package width (inches)
- `shipping_default_height` - Default package height (inches)
- `shipping_default_weight` - Default package weight (pounds)
- `shippo_api_key` - Shippo API key
- `shippo_test_mode` - Test mode flag (true/false)

### 2. `populate_shipping_from_env.py` (Optional)

**What it does:** Populates shipping settings from environment variables

**Environment variables used:**

- `SHIPPO_FROM_NAME`
- `SHIPPO_FROM_COMPANY`
- `SHIPPO_FROM_STREET1`
- `SHIPPO_FROM_STREET2`
- `SHIPPO_FROM_CITY`
- `SHIPPO_FROM_STATE`
- `SHIPPO_FROM_ZIP`
- `SHIPPO_FROM_COUNTRY`
- `SHIPPO_FROM_PHONE`
- `SHIPPO_FROM_EMAIL`
- `SHIPPO_DEFAULT_LENGTH`
- `SHIPPO_DEFAULT_WIDTH`
- `SHIPPO_DEFAULT_HEIGHT`
- `SHIPPO_DEFAULT_WEIGHT`

**Control flag:**

- Set `POPULATE_SHIPPING_FROM_ENV=true` to enable (default: true)
- Set `POPULATE_SHIPPING_FROM_ENV=false` to skip

### 3. `add_handling_fee_to_storefront_settings.py`

**What it does:** Adds handling_fee column for additional shipping charges

**Column added:**

- `handling_fee` VARCHAR(10) DEFAULT '0.00' - Additional fee added to shipping cost

**Purpose:**

- Cover packaging materials (boxes, bubble wrap, tape)
- Cover processing time and labor
- Add profit margin on shipping if desired

## Running Migrations

### Option 1: Run All Migrations (Recommended)

```bash
cd migration-service
python run-migrations.py
```

This runs ALL migrations in the correct order, including shipping migrations.

### Option 2: Run Shipping Migrations Only

```bash
cd migration-service
python run_shipping_migrations.py
```

This runs only the handling fee migration and verifies it.

### Option 3: Run with Docker/Railway

Migrations run automatically on deployment if you have the migration service configured.

## Verification

### Check if Migrations Ran Successfully

```bash
# Check if columns exist
psql $DATABASE_URL -c "
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'ecommerce_storefront_settings'
AND column_name IN ('handling_fee', 'shippo_api_key', 'shipping_from_street1')
ORDER BY column_name;
"
```

**Expected output:**

```
     column_name      |     data_type     | column_default
----------------------+-------------------+----------------
 handling_fee         | character varying | '0.00'
 shippo_api_key       | character varying |
 shipping_from_street1| character varying |
```

### Check Current Values

```bash
psql $DATABASE_URL -c "
SELECT id, user_id, store_name, handling_fee, shippo_test_mode
FROM ecommerce_storefront_settings;
"
```

### Use Debug Endpoint

Call the debug endpoint to see all settings:

```bash
curl https://your-api-url.com/api/storefront/checkout/debug/handling-fee
```

**Example response:**

```json
{
  "status": "success",
  "settings_count": 1,
  "settings": [
    {
      "id": 1,
      "user_id": "uuid-here",
      "store_name": "My Store",
      "handling_fee_raw": "2.50",
      "handling_fee_type": "str",
      "handling_fee_converted": 2.5
    }
  ],
  "first_setting_handling_fee": 2.5
}
```

## Configuration Steps

After running migrations, configure your shipping settings:

### 1. Admin Panel Configuration

1. Log into admin panel
2. Go to **CraftFlow Commerce** → **Storefront Settings**
3. Scroll to **Shipping Configuration** section
4. Fill in:
   - **Origin/Warehouse Address** - Where you ship from
   - **Default Package Dimensions** - Typical package size
   - **Shippo API Key** - Get from https://goshippo.com
   - **Test Mode** - Use "Test Mode" for development
   - **Handling Fee** - Additional fee (e.g., 2.50)
5. Click **Save Settings**

### 2. Environment Variable Configuration (Alternative)

If you prefer to use environment variables:

```bash
# Shippo API
export SHIPPO_API_KEY="shippo_live_xxxxx"
export SHIPPO_TEST_MODE="false"

# Origin Address
export SHIPPO_FROM_NAME="Your Business Name"
export SHIPPO_FROM_COMPANY="Your Company LLC"
export SHIPPO_FROM_STREET1="123 Business St"
export SHIPPO_FROM_CITY="Miami"
export SHIPPO_FROM_STATE="FL"
export SHIPPO_FROM_ZIP="33101"
export SHIPPO_FROM_COUNTRY="US"
export SHIPPO_FROM_PHONE="555-123-4567"
export SHIPPO_FROM_EMAIL="shipping@yourbusiness.com"

# Package Defaults
export SHIPPO_DEFAULT_LENGTH="10"
export SHIPPO_DEFAULT_WIDTH="8"
export SHIPPO_DEFAULT_HEIGHT="4"
export SHIPPO_DEFAULT_WEIGHT="1"

# Enable population from env vars
export POPULATE_SHIPPING_FROM_ENV="true"
```

Then run the population migration:

```bash
python run-migrations.py
```

### 3. Hybrid Approach (Recommended)

Use environment variables as defaults, then override in admin panel:

**Priority order:**

1. Database settings (highest priority)
2. Environment variables
3. Hard-coded defaults (lowest priority)

## Testing

### 1. Test Handling Fee Calculation

```bash
# Get shipping rates
curl -X POST https://your-api-url.com/api/storefront/checkout/shipping-rates \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": {
      "first_name": "Test",
      "last_name": "User",
      "address1": "123 Main St",
      "city": "Miami",
      "state": "FL",
      "zip_code": "33101",
      "country": "United States"
    }
  }'
```

**Expected response:**

```json
[
  {
    "carrier": "USPS",
    "service": "Priority Mail",
    "service_level": "usps_priority",
    "amount": 12.49, // Shippo rate (9.99) + handling fee (2.50)
    "currency": "USD",
    "estimated_days": 2,
    "duration_terms": "1-3 business days",
    "rate_id": "rate_abc123"
  }
]
```

### 2. Check Backend Logs

Look for these log messages:

```
INFO: Found StorefrontSettings for user_id: abc-123-def
INFO: Handling fee loaded: $2.50
```

### 3. Test Checkout Flow

1. Add product to cart
2. Go to checkout
3. Enter shipping address
4. **Verify:** Shipping options include handling fee
5. Select shipping method
6. **Verify:** Total includes handling fee
7. Complete checkout

## Troubleshooting

### Issue: Handling fee not applied

**Check:**

1. Migration ran successfully: `python run_shipping_migrations.py`
2. Handling fee is set in admin panel (not "0.00")
3. Debug endpoint shows correct value
4. Backend logs show "Handling fee loaded: $X.XX"

**Fix:**

```bash
# Verify migration
python run_shipping_migrations.py

# Check database
psql $DATABASE_URL -c "SELECT handling_fee FROM ecommerce_storefront_settings;"

# If empty, set in admin panel
```

### Issue: No shipping rates returned

**Check:**

1. Shippo API key is correct
2. Origin address is complete
3. Package dimensions are set
4. Test mode matches your API key (test vs live)

**Fix:**

```bash
# Check settings
curl https://your-api-url.com/api/storefront/checkout/debug/handling-fee

# Verify Shippo credentials
# Make sure shippo_api_key starts with "shippo_live_" or "shippo_test_"
```

### Issue: Migration fails

**Error: "table does not exist"**

```bash
# Run ecommerce table creation first
python run-migrations.py
```

**Error: "column already exists"**

```bash
# Migration already ran, you're good!
# Just verify with:
python run_shipping_migrations.py
```

**Error: "permission denied"**

```bash
# Check database permissions
# User needs ALTER TABLE permission
```

## Rollback

If you need to remove the handling fee feature:

```python
# Run downgrade
from migrations.add_handling_fee_to_storefront_settings import downgrade
from sqlalchemy import create_engine

engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    trans = conn.begin()
    downgrade(conn)
    trans.commit()
```

**Warning:** This will permanently delete the `handling_fee` column and all stored values.

## Support

If you encounter issues:

1. Check logs: `tail -f logs/migration.log`
2. Run verification: `python run_shipping_migrations.py`
3. Check debug endpoint: `/api/storefront/checkout/debug/handling-fee`
4. Review error messages and traceback

## Summary

✅ **3 migrations** for complete shipping feature
✅ **Handling fee** configurable per storefront
✅ **Shippo integration** for real-time rates
✅ **Database storage** with environment fallback
✅ **Debug tools** for troubleshooting
✅ **Multi-carrier** support (USPS, UPS, FedEx)

Your shipping system is now fully configured and ready to use!
