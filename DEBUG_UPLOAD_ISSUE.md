# Debug Logging for Upload Issue

## Problem

Only the last design is being uploaded to Etsy instead of all uploaded designs.

## Logging Added

I've added comprehensive debug logging at every critical point in the upload flow to identify where designs are being dropped.

### 1. Design Query (service.py:1309-1314)

**Location:** After querying designs from database

**What to look for:**

```
🔍 DEBUG: Received X design IDs from frontend
🔍 DEBUG: Design IDs: [uuid1, uuid2, uuid3, ...]
🔍 DEBUG: Queried X designs from database
🔍 DEBUG: Design 1: id=..., filename=..., file_path=...
🔍 DEBUG: Design 2: id=..., filename=..., file_path=...
```

**Expected:** Number of design IDs should match number of designs queried

**If mismatch:** Database query is filtering out some designs (check is_active flag or user_id match)

---

### 2. Filename Collection (mockups_util.py:689-705)

**Location:** When collecting filenames from design objects

**What to look for:**

```
🔍 DEBUG create_mockups_for_etsy: Processing X design objects
🔍 DEBUG: Added filename to list: design1.png
🔍 DEBUG: Added filename to list: design2.png
🔍 DEBUG: Total design_filenames collected: X
🔍 DEBUG: design_filenames list: ['design1.png', 'design2.png', ...]
```

**Expected:** Number of filenames collected should match number of designs

**If mismatch:** Some design objects don't have a filename attribute or it's None

---

### 3. Mockup Generation Result (mockups_util.py:871-872 & 1016-1020)

**Location:** After all mockups are generated

**What to look for:**

```
✅ Completed parallel mockup generation: X/Y successful
🔍 DEBUG: mockup_return dict has X entries: ['design1.png', 'design2.png', ...]
🔍 DEBUG: Returning from create_mockups_for_etsy
```

**Expected:** mockup_return should have same number of entries as design_filenames (unless some failed)

**If fewer entries:** Check for error logs showing which designs failed mockup generation:

```
❌ Failed to generate mockups for design2.png - will not be uploaded to Etsy
⚠️ WARNING: 2/5 designs failed mockup generation
```

---

### 4. Mockup Data Received (service.py:1383-1387)

**Location:** After create_mockups_for_etsy returns

**What to look for:**

```
🔍 DEBUG: mockup_data keys (filenames): ['design1.png', 'design2.png', ...]
🔍 DEBUG: mockup_data has X entries
🔍 DEBUG: Mockup for 'design1.png': Y mockup file(s)
🔍 DEBUG: Mockup for 'design2.png': Y mockup file(s)
```

**Expected:** mockup_data should match mockup_return from previous step

**If mismatch:** Data is being lost during the return/assignment

---

### 5. Etsy Upload Queue (service.py:1433-1434)

**Location:** Before starting Etsy uploads

**What to look for:**

```
DEBUG API: Creating X Etsy listings in parallel with Y workers
🔍 DEBUG: mockup_data.items() to be processed: [('design1.png', 3), ('design2.png', 3), ...]
```

**Expected:** Should show all designs that had successful mockup generation

**If fewer entries:** mockup_data was not populated correctly

---

## How to Test

1. **Upload 3-5 non-duplicate designs** through the frontend

2. **Check the Railway logs** for your server service

3. **Look for the debug logs** in order:
   - How many design IDs received?
   - How many designs queried from DB?
   - How many filenames collected?
   - How many mockups generated?
   - How many Etsy listings queued?

4. **Find the bottleneck** where the count drops

## Expected Flow

For 5 uploaded designs:

```
🔍 DEBUG: Received 5 design IDs from frontend
🔍 DEBUG: Queried 5 designs from database
🔍 DEBUG: Total design_filenames collected: 5
✅ Completed parallel mockup generation: 5/5 successful
🔍 DEBUG: mockup_data has 5 entries
DEBUG API: Creating 5 Etsy listings in parallel
```

## Common Issues to Look For

### Issue 1: Missing Filenames

```
🔍 DEBUG: Queried 5 designs from database
🔍 DEBUG: Total design_filenames collected: 1  ← PROBLEM!
```

**Cause:** Design objects in database don't have filename set
**Fix:** Check design creation logic in `/designs/` endpoint

### Issue 2: Mockup Generation Failures

```
✅ Completed parallel mockup generation: 1/5 successful  ← PROBLEM!
❌ Failed to generate mockups for design2.png
❌ Failed to generate mockups for design3.png
```

**Cause:** Mockup processing errors (check stack traces in logs)
**Fix:** Fix mockup generation code or check file paths

### Issue 3: Empty mockup_data

```
🔍 DEBUG: mockup_return has 5 entries: [...]
🔍 DEBUG: mockup_data has 0 entries  ← PROBLEM!
```

**Cause:** Data lost during return or assignment
**Fix:** Check mockup_data assignment logic

## Next Steps

1. **Run a test upload** with 3-5 designs
2. **Copy the full server logs** and send them to me
3. **I'll analyze** where the count drops and identify the exact issue
4. **We'll fix** the specific problem

The debug logs will tell us exactly where designs are being dropped!
