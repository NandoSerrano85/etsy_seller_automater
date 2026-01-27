# Railway OOM Fix Applied - Container Memory Detection

## Problem Identified

From your logs:

```
WARNING: ⚠️  Showing host memory (container memory limits not detected by psutil)
```

**Root Cause:** Railway containers don't expose cgroup memory files, so psutil sees the **host machine's memory** (32-256GB) instead of your **container's 8GB limit**.

**Impact:**

```
psutil sees: 256GB total
Pause threshold: 87% of 256GB = 222GB
Your container limit: 8GB
Result: OOM at 8GB before ever reaching 222GB pause threshold ❌
```

## Fix Applied

### 1. **Force 8GB Limit in Railway Containers** ✅

**File:** `server/src/utils/railway_memory_optimizer.py`

**What Changed:**

```python
# Detect if seeing host memory (>16GB) while in Railway/container
if total_gb > 16 and (in_railway or in_container):
    logger.warning(f"⚠️  psutil shows {total_gb:.0f}GB (host memory), forcing Railway 8GB limit")
    total_gb = RAILWAY_TOTAL_MEMORY_GB  # Force 8GB
    effective_gb = RAILWAY_EFFECTIVE_MEMORY_GB  # 7.5GB usable
```

**Now:**

- Detects Railway environment: `RAILWAY_ENVIRONMENT` env var
- Detects container: `/.dockerenv` or `/run/.containerenv` file
- If psutil shows >16GB in Railway/container → Force 8GB limit
- Pause threshold correctly calculated as 87% of 8GB = 6.96GB ✅

### 2. **More Aggressive Thresholds** ✅

**Old Thresholds:**

```python
MEMORY_PAUSE_THRESHOLD = 0.87     # 87% = 6.50GB (only 1.5GB headroom)
MEMORY_CRITICAL_THRESHOLD = 0.80  # 80% = 6.00GB
```

**New Thresholds (Railway-optimized):**

```python
MEMORY_PAUSE_THRESHOLD = 0.80     # 80% = 6.00GB (2.0GB headroom!)
MEMORY_CRITICAL_THRESHOLD = 0.75  # 75% = 5.62GB (abort new allocations earlier)
MEMORY_EMERGENCY_THRESHOLD = 0.87 # 87% = 6.50GB (was 93%)
```

**Why:** Without cgroup access, we need more headroom to safely cleanup and resume.

### 3. **More Frequent Memory Checks** ✅

**Old:** Check every 10 item placements

**New:** Check every 5 item placements

**Why:** Catch memory spikes faster in Railway environment.

## Expected Behavior Now

### Startup Logs:

```
🚂 Railway Memory Monitor initialized
   Container memory limit detection: ⚠️  psutil fallback

🚂 RAILWAY CONTAINER DIAGNOSTICS
📊 CGROUP MEMORY LIMITS:
   No cgroup memory limits found
   Will use psutil (may show host memory, not container)

📊 PSUTIL DETECTION:
   Total memory (may be host): 256.00GB
   ⚠️  Showing host memory (container memory limits not detected by psutil)

🚂 Railway Memory: 2.35GB / 8.00GB (31.3%)  ← CORRECTED!
   Detection method: psutil_railway_corrected
   ⚠️  psutil shows 256GB (host memory), forcing Railway 8GB limit
```

### During Gang Sheet Creation:

```
Placing item 75...
   Progress: 75 items placed, Memory: 5.20GB (69.3%)

Placing item 100...
   Progress: 100 items placed, Memory: 6.05GB (80.7%)

⏸️  PAUSE 1: Memory at 6.08GB (81.1%)  ← NOW PAUSES!
   Phase: Gang sheet part 1, 100 items placed
   Threshold: 80.0% (6.00GB)
   🧹 Attempting cleanup to 5.25GB...

🧹 AGGRESSIVE MEMORY CLEANUP (Railway Optimization)
   Before: 6.08GB (81.1%)
   Running full GC...
   GC collected 2345 objects in 8 cycles
   malloc_trim: freed memory to OS
   After cleanup: 5.50GB (73.3%)
   ✅ Freed 0.58GB immediately
   🎯 Target: 5.25GB, waiting up to 30s...
   ✅ Target achieved in 12.3s
   Final: 5.10GB (68.0%)
   Total freed: 0.98GB
   ✅ Cleanup successful, resuming work

Placing item 101...
... continues successfully ...
```

### Success Summary:

```
======================================================================
🚂 RAILWAY MEMORY SUMMARY
======================================================================
✅ Gang sheet creation completed successfully
📊 Total parts created: 2

💾 Final Memory Usage:
   Current: 3.45GB / 8.00GB (43.1%)
   Peak: 6.40GB (never hit 8GB!)
   Available: 4.55GB

🧹 Memory Management:
   Pauses for cleanup: 3
   Total cleanups: 5
======================================================================
```

## What Changed - Summary

| Aspect               | Before               | After                      |
| -------------------- | -------------------- | -------------------------- |
| **Memory Detection** | Shows 256GB (host)   | Forces 8GB (Railway limit) |
| **Pause Threshold**  | 87% of 256GB = 222GB | 80% of 8GB = 6.0GB         |
| **Would Pause?**     | Never (OOM first)    | Yes at 6.0GB!              |
| **Check Frequency**  | Every 10 items       | Every 5 items              |
| **Headroom**         | 1.5GB                | 2.0GB                      |

## Files Modified

1. ✅ `server/src/utils/railway_memory_optimizer.py`
   - Added Railway/container detection
   - Force 8GB limit when seeing host memory
   - Lowered thresholds for Railway

2. ✅ `server/src/utils/gangsheet_engine.py`
   - Check memory every 5 items instead of 10
   - More frequent pause opportunities

## Test This Fix

### Quick Test:

Create a small gang sheet and look for these logs:

**Should see:**

```
⚠️  psutil shows 256GB (host memory), forcing Railway 8GB limit
🚂 Railway Memory: X.XXG / 8.00GB (XX.X%)
   Detection method: psutil_railway_corrected
```

**Should NOT see:**

```
🚂 Railway Memory: X.XXG / 256.00GB (0.X%)  ← WRONG!
```

### Full Test:

Create a large gang sheet (15-20 orders):

**Expected:**

- Pauses at ~6GB (80%)
- Cleans up aggressively
- Resumes work
- Completes successfully
- Shows pause count in summary

**Should NOT:**

- OOM kill with no logs
- Show memory percent stuck at low values (1-3%)

## If Still Getting OOM

### Scenario 1: Memory Spikes Between Checks

**Logs show:** No pause, just OOM

**Fix:** Reduce to every 3 items:

```python
if images_processed_in_part % 3 == 0:  # Even more frequent
```

### Scenario 2: Cleanup Not Freeing Enough

**Logs show:** Pause at 6GB, cleanup only frees 0.2GB

**Fix:** Lower pause threshold to 70%:

```python
MEMORY_PAUSE_THRESHOLD = 0.70  # 70% = 5.25GB
```

### Scenario 3: Gang Sheets Too Large

**Logs show:** Pause works but gang sheet allocation itself is >2GB

**Fix:** Already have MAX_GANG_SHEET_MEMORY_GB = 3.0, lower to 2.0:

```python
MAX_GANG_SHEET_MEMORY_GB = 2.0  # Reduce from 3.0
```

## Verification

Run a test and check your logs for:

1. ✅ `forcing Railway 8GB limit` message
2. ✅ Memory shown as `X.XX / 8.00GB` not `/ 256.00GB`
3. ✅ Detection method: `psutil_railway_corrected`
4. ✅ Pause messages when memory hits 80%
5. ✅ Final summary showing pauses and cleanups

## Why This Fixes OOM

**Before:**

- Thought it had 256GB
- Pause at 222GB
- OOM at 8GB (no pause, no logs)

**After:**

- Knows it has 8GB
- Pause at 6GB
- Cleanup → 5GB
- Resume → Success!

## Summary

**Problem:** psutil showed host memory (256GB) instead of container limit (8GB)

**Fix:** Detect Railway environment and force 8GB limit when seeing >16GB

**Result:** Pause system now works because thresholds are calculated correctly

**Thresholds:** Lowered pause from 87% to 80% for more headroom in Railway

**Checks:** Every 5 items instead of 10 for faster detection

**Expected:** No more silent OOM crashes! Will pause, cleanup, resume automatically.
