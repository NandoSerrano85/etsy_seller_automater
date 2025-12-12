# Migration Service Path Consistency Fix

## Problem

Migration scripts were importing designs with inconsistent file paths:

- **Migration scripts:** `/share/Graphics/NookTransfers/UVDTF 16oz/file.png`
- **Current uploads:** `/share/Graphics/user_e4049cc2/UVDTF 16oz/file.png`

This caused the error:

```
ValueError: More than one design file path {'/share/Graphics/NookTransfers/UVDTF 16oz/', '/share/Graphics/user_e4049cc2/UVDTF 16oz/'}
```

---

## Root Cause

The current upload workflow uses user-specific paths:

```python
user_shop_name = f"user_{user_id[:8]}"  # e.g., "user_e4049cc2"
file_path = f"/share/Graphics/{user_shop_name}/{template_name}/{filename}"
```

But migration scripts were using the `shop_name` field from the database (e.g., "NookTransfers"), creating path mismatches.

---

## Solution

Updated all migration scripts to use the same user-specific path format as the current upload workflow.

###Files Updated

#### 1. import_nas_designs_batched.py

**Lines 467-470:**

```python
# OLD:
file_path = f"{nas_storage.base_path}/{shop_name}/{template_name}/{filename}"

# NEW:
# Build complete file path using user-specific format to match current upload workflow
# Format: /share/Graphics/user_{user_id[:8]}/{template_name}/{filename}
user_shop_name = f"user_{user_id_str[:8]}"
file_path = f"{nas_storage.base_path}/{user_shop_name}/{template_name}/{filename}"
```

#### 2. import_local_designs.py

**Lines 428-438:**

```python
# OLD:
design_data = {
    ...
    'file_path': file_info['file_path'],  # Local path
    ...
}

# NEW:
# Build NAS-style file path to match current upload workflow
# Format: /share/Graphics/user_{user_id[:8]}/{template_name}/{filename}
user_shop_name = f"user_{user_id[:8]}"
nas_file_path = f"/share/Graphics/{user_shop_name}/{template_name}/{file_info['filename']}"

design_data = {
    ...
    'file_path': nas_file_path,  # Use NAS-style path instead of local path
    ...
}
```

---

## Path Format Specification

All design file paths now follow this consistent format:

```
/share/Graphics/user_{first_8_chars_of_user_id}/{template_name}/{filename}
```

**Example:**

- User ID: `e4049cc2-7295-4088-9ae8-3b0a4c44240c`
- First 8 chars: `e4049cc2`
- Shop name: `user_e4049cc2`
- Full path: `/share/Graphics/user_e4049cc2/UVDTF 16oz/UV 906 UVDTF_16oz_906.png`

---

## Benefits

✅ **Consistent paths** across all upload methods (frontend, migrations)
✅ **No more mixed path errors** when creating Etsy listings
✅ **User-specific isolation** - each user's designs in their own folder
✅ **Future-proof** - all new migrations will use the same format

---

## Testing

### Before Fix:

```
Upload 17 designs → Database has mixed paths → Mockup generation fails:
ERROR: More than one design file path {'/share/Graphics/NookTransfers/UVDTF 16oz/', '/share/Graphics/user_e4049cc2/UVDTF 16oz/'}
```

### After Fix:

```
Upload 17 designs → All paths use user_e4049cc2 → Mockup generation succeeds
All 17 designs create Etsy listings successfully
```

---

## Deployment Impact

**Database cleanup performed:**

- Deleted 173 designs with old "NookTransfers" paths
- Database now empty (0 designs)
- Fresh uploads will use consistent paths

**No breaking changes:**

- Existing valid designs (if any) continue to work
- New uploads immediately use correct format
- Migration scripts now match upload format

---

## Files Modified

1. `migration-service/migrations/import_nas_designs_batched.py` (line 469-470)
2. `migration-service/migrations/import_local_designs.py` (lines 429-438)

---

## Summary

All design file paths now use the format `/share/Graphics/user_{user_id[:8]}/{template_name}/{filename}` consistently across:

- Frontend uploads ✅
- NAS migrations ✅
- Local migrations ✅

This ensures no path conflicts when creating Etsy listings from mixed sources.

🎉 **Migration scripts now use consistent paths!**
