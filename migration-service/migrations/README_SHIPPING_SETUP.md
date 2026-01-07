# Shipping Configuration Setup Guide

This guide explains how to set up Shippo shipping integration using the **Hybrid Approach** (Option 3).

## Quick Start

### Step 1: Railway Environment Variables

Add these to your Railway service as **fallback defaults**:

```bash
# Required - Fallback API Key
SHIPPO_API_KEY=shippo_live_your_api_key_here

# Optional - Test mode (default: true)
SHIPPO_TEST_MODE=false

# Optional - Fallback origin address
SHIPPO_FROM_NAME=Your Business Name
SHIPPO_FROM_COMPANY=Your Company LLC
SHIPPO_FROM_STREET1=123 Business St
SHIPPO_FROM_STREET2=Suite 100
SHIPPO_FROM_CITY=Miami
SHIPPO_FROM_STATE=FL
SHIPPO_FROM_ZIP=33101
SHIPPO_FROM_COUNTRY=US
SHIPPO_FROM_PHONE=555-123-4567
SHIPPO_FROM_EMAIL=shipping@yourbusiness.com

# Optional - Fallback package dimensions (inches and pounds)
SHIPPO_DEFAULT_LENGTH=10
SHIPPO_DEFAULT_WIDTH=8
SHIPPO_DEFAULT_HEIGHT=4
SHIPPO_DEFAULT_WEIGHT=1

# Optional - Auto-populate database from environment variables
POPULATE_SHIPPING_FROM_ENV=true
```

### Step 2: Deploy and Run Migrations

When you deploy to Railway, these migrations will run automatically:

1. **add_shipping_config_to_storefront_settings** - Adds database columns
2. **populate_shipping_from_env** - Populates database from environment variables (if `POPULATE_SHIPPING_FROM_ENV=true`)

### Step 3: Configure Through Admin UI (Optional)

Go to **CraftFlow > Storefront Settings > Shipping Configuration** to:

- Update warehouse address
- Change package dimensions
- Use a different Shippo API key
- Toggle test mode

## How It Works

### Priority Order

The Shippo service checks settings in this order:

1. **Database** (from StorefrontSettings table) ← **FIRST**
2. **Environment Variables** (from Railway) ← **FALLBACK**
3. **Hard-coded Defaults** ← **LAST RESORT**

### Example Flow

```
Customer checks out
    ↓
Shippo service needs API key
    ↓
Check database: shippo_api_key column
    ├─ If populated → Use database value ✅
    └─ If NULL → Check SHIPPO_API_KEY environment variable ✅

Shippo service needs warehouse address
    ↓
Check database: shipping_from_street1 column
    ├─ If populated → Use database address ✅
    └─ If NULL → Check SHIPPO_FROM_* environment variables ✅
```

## Migration: populate_shipping_from_env

This optional migration:

- ✅ Runs automatically if `POPULATE_SHIPPING_FROM_ENV=true` (default)
- ✅ Reads environment variables
- ✅ Populates the first user's storefront settings
- ✅ Only runs if settings are empty (won't overwrite existing data)
- ✅ Can be disabled by setting `POPULATE_SHIPPING_FROM_ENV=false`

### What It Does

```
1. Checks if ecommerce_storefront_settings table exists
2. Finds the first user's settings
3. Checks if shipping settings are already populated
   └─ If populated → Skip (no overwrite)
   └─ If empty → Read environment variables and populate
4. Updates database with non-empty environment values
5. Logs which fields were populated
```

### Disabling Auto-Population

To prevent automatic population from environment variables:

```bash
POPULATE_SHIPPING_FROM_ENV=false
```

This is useful if you want to:

- Configure everything manually through the UI
- Keep environment variables as fallback only
- Prevent accidental overwrites

## Use Cases

### Use Case 1: Quick Start

**Goal**: Get shipping working immediately

1. Set all `SHIPPO_*` environment variables in Railway
2. Deploy
3. Migration auto-populates database
4. Shipping works instantly ✅

### Use Case 2: Database-First

**Goal**: Configure through UI only

1. Set only `SHIPPO_API_KEY` in Railway (as backup)
2. Set `POPULATE_SHIPPING_FROM_ENV=false`
3. Deploy
4. Configure address/dimensions through admin UI
5. Database settings override environment ✅

### Use Case 3: Hybrid (Recommended)

**Goal**: Fallbacks + UI flexibility

1. Set all environment variables as defaults
2. Leave `POPULATE_SHIPPING_FROM_ENV=true`
3. Deploy - database gets populated
4. Later, update specific settings through UI as needed
5. Database overrides take effect immediately ✅

## Benefits

✅ **No redeploys needed** - Update warehouse address through UI
✅ **Multi-tenant ready** - Each user can have their own settings
✅ **Safety net** - Falls back to environment variables if database is empty
✅ **Flexible** - Can test with different API keys per user
✅ **Easy migration** - Automatically populates from existing env vars

## Troubleshooting

### Shipping rates showing fallback values

**Cause**: No API key configured
**Fix**: Check database has `shippo_api_key` OR set `SHIPPO_API_KEY` in Railway

### Shipping rates using wrong warehouse address

**Cause**: Database settings taking priority
**Fix**:

1. Go to Storefront Settings > Shipping Configuration
2. Update warehouse address
3. Save
4. OR clear database values to fall back to environment variables

### Migration didn't populate database

**Cause**: `POPULATE_SHIPPING_FROM_ENV=false` or settings already existed
**Check**:

```sql
SELECT shipping_from_street1, shippo_api_key
FROM ecommerce_storefront_settings;
```

**Fix**: Manually populate through admin UI

## Environment Variables Reference

| Variable                     | Required | Default                  | Description               |
| ---------------------------- | -------- | ------------------------ | ------------------------- |
| `SHIPPO_API_KEY`             | No\*     | -                        | Shippo API key (fallback) |
| `SHIPPO_TEST_MODE`           | No       | `true`                   | Test or live mode         |
| `SHIPPO_FROM_NAME`           | No       | `CraftFlow Commerce`     | Business name             |
| `SHIPPO_FROM_COMPANY`        | No       | `CraftFlow Commerce`     | Company name              |
| `SHIPPO_FROM_STREET1`        | No       | `123 Business St`        | Street address            |
| `SHIPPO_FROM_STREET2`        | No       | -                        | Suite/Apt (optional)      |
| `SHIPPO_FROM_CITY`           | No       | `Miami`                  | City                      |
| `SHIPPO_FROM_STATE`          | No       | `FL`                     | State (2-letter)          |
| `SHIPPO_FROM_ZIP`            | No       | `33101`                  | ZIP code                  |
| `SHIPPO_FROM_COUNTRY`        | No       | `US`                     | Country (2-letter)        |
| `SHIPPO_FROM_PHONE`          | No       | `555-0100`               | Phone number              |
| `SHIPPO_FROM_EMAIL`          | No       | `shipping@craftflow.com` | Email                     |
| `SHIPPO_DEFAULT_LENGTH`      | No       | `10`                     | Package length (inches)   |
| `SHIPPO_DEFAULT_WIDTH`       | No       | `8`                      | Package width (inches)    |
| `SHIPPO_DEFAULT_HEIGHT`      | No       | `4`                      | Package height (inches)   |
| `SHIPPO_DEFAULT_WEIGHT`      | No       | `1`                      | Package weight (pounds)   |
| `POPULATE_SHIPPING_FROM_ENV` | No       | `true`                   | Auto-populate database    |

\* Either `SHIPPO_API_KEY` environment variable OR database `shippo_api_key` is required for real-time rates. If neither is set, fallback static rates are used.

## Next Steps

After setup:

1. Test checkout to verify shipping rates appear
2. Update settings through admin UI as needed
3. Monitor Shippo dashboard for API usage
4. Switch from test mode to live mode when ready

For more information, see: https://goshippo.com/docs/
