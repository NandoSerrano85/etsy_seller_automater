# Print Files Backend Crash - Fixed

## Problem

Backend was crashing when clicking "Send to Print" → "Create Print Files" in admin-frontend's Etsy Orders section.

## Root Cause

After updating the code to use `etsy_stores.shop_name` instead of `user.shop_name`, the endpoint was failing for users who don't have an `etsy_stores` record yet (using legacy `user.shop_name` field).

## Fixes Applied

### 1. Shop Name Fallback Logic

**Files Updated:**

- `server/src/routes/orders/service.py` (3 functions)
- `server/src/routes/orders/controller.py` (2 endpoints)

**New Logic:**

```python
# Try etsy_stores table first
shop_name = get_etsy_shop_name(db, user_id)

# Fallback to user.shop_name if not found
if not shop_name or shop_name.startswith("user_"):
    shop_name = user.shop_name if hasattr(user, 'shop_name') else None

    # Only fail if neither exists
    if not shop_name:
        raise HTTPException(status_code=400, detail="No shop name configured")
```

**Why This Works:**

- ✅ Users with `etsy_stores` records → uses proper shop name from table
- ✅ Legacy users with `user.shop_name` → falls back gracefully
- ❌ Users with neither → clear error message

### 2. Enhanced Error Logging

Added comprehensive logging throughout the flow to pinpoint crashes:

```python
logging.info("🚀 create_print_files: Starting request")
logging.info(f"📋 User ID: {user_id}")
logging.info(f"✅ EtsyAPI initialized")
logging.info(f"📋 Template name: {template_name}")
logging.info(f"📋 Shop name from etsy_stores: {shop_name}")
logging.info(f"✅ fetch_open_orders_items_nas completed")
```

**Error Logging:**

```python
except Exception as e:
    logging.error(f"❌ Error creating print files: {str(e)}")
    logging.error(f"📋 Full traceback:\n{traceback.format_exc()}")
```

### 3. Proper Exception Propagation

Updated exception handling to distinguish between:

- `HTTPException` - Re-raised with proper status codes
- `Exception` - Caught, logged, and returned as error response

**Controller:**

```python
except HTTPException as http_exc:
    # Re-raise with proper status code
    logging.error(f"❌ HTTP Exception: {http_exc.status_code}")
    raise
except Exception as e:
    # Log and return 500
    logging.error(f"❌ Error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
```

## How to Debug on Railway

### Step 1: Check Railway Logs

After deploying, monitor Railway logs for the new emoji markers:

```bash
# Railway Dashboard → Your Service → Deployments → View Logs

# Look for these markers in order:
🚀 create_print_files: Starting request        # Request received
📋 User ID: <uuid>                              # User identified
✅ EtsyAPI initialized                          # API ready
📋 Template name: UVDTF 16oz                   # Template loaded
📋 Shop name from etsy_stores: <name>          # Shop name lookup
✅ Creating print files for user...            # Process started
🔵 Using NAS storage                            # NAS mode
✅ fetch_open_orders_items_nas completed       # Etsy API success
✅ Downloaded X files, ⚠️ skipped Y files      # File download done
✅ Print file creation completed               # Success!
```

### Step 2: Identify Crash Point

**If logs stop at:**

| Last Log Entry                   | Problem                | Solution                                    |
| -------------------------------- | ---------------------- | ------------------------------------------- |
| `🚀 Starting request`            | Controller crash       | Check FastAPI/DB connection                 |
| `📋 User ID:`                    | User not found         | Verify user exists in DB                    |
| `✅ EtsyAPI initialized`         | Template query failing | Check DB schema                             |
| `📋 Shop name from etsy_stores:` | No shop name           | User needs to connect Etsy or set shop_name |
| `🔵 Using NAS storage`           | NAS connection failing | Verify NAS credentials/network              |
| `✅ fetch_open_orders_items_nas` | Etsy API error         | Check Etsy OAuth tokens                     |
| File download section            | Missing files          | Upload design files to NAS                  |
| Gang sheet creation              | Image processing error | Check printer/canvas config                 |

### Step 3: Common Errors and Solutions

#### Error: "No shop name configured"

**Cause:** User has neither `etsy_stores` record nor `user.shop_name`

**Solution:**

```sql
-- Option 1: Set user.shop_name (temporary)
UPDATE users SET shop_name = 'YourEtsyShopName' WHERE email = 'user@example.com';

-- Option 2: Create etsy_stores record (proper)
INSERT INTO etsy_stores (id, user_id, shop_name, etsy_shop_id, is_active, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  '<user_id>',
  'YourEtsyShopName',
  '<etsy_shop_id>',
  true,
  NOW(),
  NOW()
);
```

#### Error: "Failed to download design file from NAS"

**Cause:** Design files don't exist on NAS

**Solution:**

- Upload missing files to NAS: `/share/Graphics/<shop_name>/UVDTF 16oz/`
- Or system will skip them gracefully (new behavior)

#### Error: "No valid design files found"

**Cause:** ALL design files are missing

**Solution:**

- Upload at least one valid design file
- Or check if orders actually have designs assigned

#### Error: "Etsy API authentication failed"

**Cause:** OAuth tokens expired

**Solution:**

- Go to admin-frontend → Etsy → Settings
- Click "Reconnect" to refresh OAuth tokens

## Testing Checklist

After deploying to Railway:

- [ ] Check Railway logs show `🚀 Starting request`
- [ ] Verify shop name is resolved correctly
- [ ] Confirm NAS connection works (`🔵 Using NAS storage`)
- [ ] Check file downloads complete (`✅ Downloaded X files`)
- [ ] Verify gang sheets are created
- [ ] Test with missing files (should skip gracefully)
- [ ] Test with no files (should return clear error)

## Expected Behavior Now

### Success (All Files Available)

```json
{
  "success": true,
  "message": "Print files created successfully - 5 sheets generated",
  "sheets_created": 5,
  "files_downloaded": 31,
  "files_skipped": 0
}
```

### Success (Some Files Missing)

```json
{
  "success": true,
  "message": "Print files created successfully - 3 sheets (⚠️ 6 missing files skipped)",
  "sheets_created": 3,
  "files_downloaded": 25,
  "files_skipped": 6
}
```

### Error (All Files Missing)

```json
{
  "success": false,
  "error": "No design files available. 31 files were missing.",
  "skipped_files": 31
}
```

### Error (No Shop Configured)

```json
{
  "success": false,
  "error": "No shop name configured. Please connect your Etsy store or set shop name in settings."
}
```

## Files Modified

1. `server/src/routes/orders/service.py`:
   - Added shop name fallback logic (3 functions)
   - Enhanced logging throughout
   - Improved exception handling

2. `server/src/routes/orders/controller.py`:
   - Added shop name fallback logic (2 endpoints)
   - Enhanced logging
   - Proper HTTPException propagation

## Next Steps

1. **Deploy to Railway:**

   ```bash
   git add .
   git commit -m "Fix print files crash - add shop_name fallback and enhanced logging"
   git push origin main
   ```

2. **Monitor Logs:** Watch Railway logs when clicking "Create Print Files"

3. **Check Error Messages:** Any errors should now have clear, actionable messages

4. **Report Issues:** If still crashing, share:
   - Last log entry before crash (with emoji marker)
   - Full error message from logs
   - User's shop configuration (has etsy_stores record? has user.shop_name?)

## Summary

**Before:** Backend crashed silently when shop name wasn't found
**After:** Graceful fallback to user.shop_name with detailed error logging

**Before:** No way to debug where crash occurred
**After:** Emoji markers at each step make debugging easy

**Before:** Required etsy_stores record to work
**After:** Works with etsy_stores OR user.shop_name

The system is now more resilient and debuggable!
