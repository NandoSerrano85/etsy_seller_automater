# Railway OOM Debugging Guide

## Still Getting OOM? Here's How to Debug

Since I can't log into Railway directly, here's what you need to check:

## Step 1: Run Diagnostic Script in Railway

Add this endpoint to your API or run directly in Railway:

```bash
# In Railway shell or as startup command:
python server/test_railway_memory.py
```

This will show:

- ✅ If cgroup memory limits are detected (accurate)
- ⚠️ If using psutil fallback (may be wrong)
- What memory limits Railway sees
- If pause system will work

## Step 2: Check Railway Logs During Gang Sheet Creation

Look for these log lines at the START:

### Good (cgroup detected):

```
🚂 RAILWAY CONTAINER DIAGNOSTICS
Running in container: True
📊 CGROUP MEMORY LIMITS:
   cgroup v1 detected: ✅
   Container memory limit: 8.00GB
   Current usage: 2.35GB (29.4%)

🚂 Railway Memory: 2.35GB / 8.00GB (29.4%)
   Detection method: cgroup_v1
   ✅ Using container memory limits (accurate for Railway)
```

### Bad (psutil fallback):

```
🚂 RAILWAY CONTAINER DIAGNOSTICS
Running in container: True
📊 CGROUP MEMORY LIMITS:
   No cgroup memory limits found
   Will use psutil (may show host memory, not container)

📊 PSUTIL DETECTION:
   psutil available: ✅
   Total memory (may be host): 256.00GB  ← WRONG! Showing host
   ⚠️  Showing host memory (container memory limits not detected by psutil)

🚂 Railway Memory: 2.35GB / 256.00GB (0.9%)  ← WRONG percentage!
   Detection method: psutil
   ⚠️  Using host memory detection (may be inaccurate in containers)
```

## Step 3: What's Wrong?

### Problem A: cgroup Not Detected

**Cause:** Railway container doesn't expose cgroup memory files

**Fix:** Added fallback to Railway default (8GB)

**Check logs for:**

```
⚠️  Limit seems unlimited (256.00GB), using Railway default
```

### Problem B: Memory Spikes Too Fast

**Symptom:** No pause logs, just OOM

**Cause:** Memory goes from 60% → 95% between checks (every 10 items)

**Fix:** Reduce check interval to every 5 items:

```python
# In gangsheet_engine.py, change:
if images_processed_in_part % 10 == 0:  # Current
# To:
if images_processed_in_part % 5 == 0:  # More frequent
```

### Problem C: Pause Threshold Too High

**Symptom:** Pause logs appear but still OOM

**Cause:** 87% threshold leaves only 1GB headroom (7GB → 8GB)

**Fix:** Lower pause threshold to 80%:

```python
# In railway_memory_optimizer.py:
MEMORY_PAUSE_THRESHOLD = 0.80  # Was 0.87
```

### Problem D: Cleanup Doesn't Free Enough

**Symptom:** Logs show pause, cleanup, but only frees small amount

```
⏸️  PAUSE 1: Memory at 6.52GB (87%)
🧹 AGGRESSIVE MEMORY CLEANUP
   ✅ Freed 0.12GB  ← Too small!
   After: 6.40GB
❌ Memory still critical
```

**Causes:**

1. Gang sheet still in memory (memory-mapped but not released)
2. Python holding references
3. OS not releasing memory fast enough

**Fix:** Already implemented - wait up to 30s for OS release

### Problem E: Railway Has Lower Memory Limit

**Symptom:** Container thinks it has 8GB, but Railway kills at lower

**Check:** What Railway plan are you on?

- Hobby: 8GB (should work)
- Trial: 512MB-1GB (will definitely OOM)
- Pro: 32GB (should never OOM)

**Fix:** Upgrade plan or reduce gang sheet dimensions

## Step 4: Get Me These Logs

To help debug, please share:

1. **Diagnostic output:**

   ```bash
   python server/test_railway_memory.py
   ```

2. **First 100 lines of gang sheet creation logs:**
   - Should include the diagnostic output
   - Shows detection method
   - Shows if pause happened

3. **Railway settings:**
   - What plan? (Hobby/Trial/Pro)
   - Memory limit shown in Railway dashboard
   - Any custom memory settings?

4. **Last log line before crash:**
   - What was happening when OOM occurred?
   - Was there a pause attempt?
   - What was the memory percent?

## Step 5: Quick Fixes to Try

### Fix 1: More Aggressive Pausing

```python
# In railway_memory_optimizer.py:
MEMORY_PAUSE_THRESHOLD = 0.75  # Pause at 75% instead of 87%
```

### Fix 2: More Frequent Checks

```python
# In gangsheet_engine.py:
if images_processed_in_part % 5 == 0:  # Check every 5 instead of 10
```

### Fix 3: Lower Gang Sheet Dimensions

```python
# In printer settings or railway_memory_optimizer.py:
MAX_GANG_SHEET_MEMORY_GB = 2.0  # Was 3.0
MAX_GANG_SHEET_DIMENSION_PIXELS = 75000  # Was 100000
```

### Fix 4: Force Smaller Batches

Process fewer orders at a time:

- Current: All selected orders
- Try: 5-10 orders max per batch

## Step 6: Nuclear Option - Disable Gang Sheets Over Certain Size

Add to gangsheet_engine.py after dimension calculation:

```python
# Emergency: Abort if gang sheet would be > 2GB
if memory_gb > 2.0:
    logging.error(f"❌ Gang sheet too large: {memory_gb:.2f}GB")
    logging.error(f"   Reduce max_height_inches to create smaller gang sheets")
    return None
```

## Common Scenarios

### Scenario 1: Detection Working But Still OOM

**Logs show:**

```
✅ Using container memory limits (accurate)
Memory: 5.2GB / 8.0GB (65%)
... no pause logs ...
[OOM KILL]
```

**Diagnosis:** Memory spiking too fast between checks

**Fix:** Check every 5 items instead of 10

---

### Scenario 2: Detection Not Working

**Logs show:**

```
⚠️  Using host memory detection
Memory: 2.5GB / 256.0GB (1%)
```

**Diagnosis:** Can't see container limits, thinks it has 256GB

**Fix:** Code now uses Railway default (8GB) as fallback

---

### Scenario 3: Pause But No Recovery

**Logs show:**

```
⏸️  PAUSE 1: Memory at 6.5GB
🧹 Cleanup freed 0.15GB
❌ Memory still critical: 6.35GB
```

**Diagnosis:** Cleanup not freeing enough

**Fix:**

1. Lower pause threshold to 75%
2. Reduce max gang sheet memory to 2GB
3. Process fewer orders per batch

## Expected Healthy Logs

```
======================================================================
🚂 RAILWAY CONTAINER DIAGNOSTICS
======================================================================
Running in container: True

📊 CGROUP MEMORY LIMITS:
   cgroup v1 detected: ✅
   Container memory limit: 8.00GB
   Current usage: 2.35GB (29.4%)

📊 PSUTIL DETECTION:
   psutil available: ✅
   Total memory (may be host): 8.00GB
======================================================================

🚂 Railway Memory: 2.35GB / 8.00GB (29.4%)
   Detection method: cgroup_v1
   ✅ Using container memory limits (accurate for Railway)

📐 Requested dimensions: 16.0"×215.0" @ 400 DPI
📐 Dimensions OK: 16.0"×215.0" = 6400×86000px @ 400 DPI
   Memory requirement: 2.10GB

Placing item 50...
   Progress: 50 items placed, Memory: 4.20GB (52.5%)

Placing item 100...
   Progress: 100 items placed, Memory: 5.80GB (72.5%)

Placing item 150...
   Progress: 150 items placed, Memory: 6.45GB (80.6%)

⏸️  PAUSE 1: Memory at 6.52GB (81.5%)
   Phase: Gang sheet part 1, 150 items placed
   🧹 Attempting cleanup to 6.00GB...
   ✅ Freed 1.12GB
   Final: 5.40GB (67.5%)
   ✅ Cleanup successful, resuming work

Placing item 151...
... continues successfully ...

======================================================================
🚂 RAILWAY MEMORY SUMMARY
======================================================================
✅ Gang sheet creation completed successfully
📊 Total parts created: 2

💾 Final Memory Usage:
   Current: 3.45GB / 8.00GB (43.1%)
   Peak: 6.80GB
   Available: 4.55GB

🧹 Memory Management:
   Pauses for cleanup: 2
   Total cleanups: 4
======================================================================
```

## Files to Check

1. **`server/test_railway_memory.py`** - Run this first!
2. **`server/src/utils/railway_diagnostics.py`** - Diagnostic functions
3. **`server/src/utils/railway_memory_optimizer.py`** - Memory detection
4. **`server/src/utils/gangsheet_engine.py`** - Pause integration

## Summary

**Can't log into Railway, but you can:**

1. Run `python server/test_railway_memory.py` in Railway
2. Share the diagnostic output
3. Share first 100 lines of gang sheet creation
4. Share what Railway plan you're using
5. Share last log line before OOM

**Then I can tell you:**

- If detection is working
- Why pause isn't triggering
- What threshold to use
- How to fix your specific case

**Quick fix to try NOW:**

```python
# In railway_memory_optimizer.py, change:
MEMORY_PAUSE_THRESHOLD = 0.75  # Was 0.87 - pause earlier
```

And in gangsheet_engine.py:

```python
# Change:
if images_processed_in_part % 5 == 0:  # Was 10 - check more often
```
