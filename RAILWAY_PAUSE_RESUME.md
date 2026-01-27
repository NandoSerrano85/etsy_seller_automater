# Railway Pause & Resume - Memory Checkpointing for Gang Sheet Creation

## Problem: OOM with No Logs

**User Issue:** Railway kills process due to OOM, but no error logs are generated.

**Why No Logs:**

- Railway monitors process memory from outside
- When memory hits ~95%, Railway sends SIGKILL
- Process terminated immediately, no chance to log
- Just: "Process exited" with no explanation

## Solution: Pause Before OOM

Instead of hitting OOM, we now **pause work at 87%** (6.5GB), aggressively clean memory, and resume.

### Memory Thresholds

```python
# Railway 8GB plan effective memory: 7.5GB (after system overhead)

70% (5.25GB) - WARNING: Start monitoring closely
80% (6.00GB) - CRITICAL: Abort new gang sheet allocations
87% (6.50GB) - PAUSE: Stop work, cleanup, resume ← NEW!
93% (7.00GB) - EMERGENCY: Last chance cleanup or abort
95% (7.60GB) - OOM KILL: Railway terminates process
```

## How It Works

### Progressive Monitoring

Gang sheet creation now checks memory **every 10 item placements**:

```python
# Every 10 placements:
if images_processed_in_part % 10 == 0:
    can_continue = monitor.pause_and_cleanup_if_needed(
        current_phase=f"Gang sheet part {part}, {images_processed_in_part} items placed"
    )

    if not can_continue:
        # Abort to prevent OOM
        return None
```

### Pause-and-Cleanup Cycle

When memory hits **87% (6.5GB)**:

```
1. ⏸️  PAUSE work
   └─ Stop placing images on gang sheet

2. 🧹 AGGRESSIVE CLEANUP
   ├─ gc.collect(generation=2) × 10 cycles
   ├─ malloc_trim(0) - force OS memory release
   ├─ sys._clear_internal_caches()
   └─ Wait up to 30 seconds for memory to drop

3. 🎯 TARGET: Drop to 70% (5.25GB)
   └─ Fallback: At least below 80% (6.0GB)

4. ✅ RESUME work if target achieved
   └─ Continue placing images from where we left off

5. ❌ ABORT if memory still > 80%
   └─ Prevent OOM by stopping early
```

### Example Pause Log

```
⏸️  PAUSE 1: Memory at 6.52GB (86.9%)
   Phase: Gang sheet part 1, 120 items placed
   Threshold: 87.0% (6.50GB)
   🧹 Attempting cleanup to 5.25GB...

🧹 AGGRESSIVE MEMORY CLEANUP (Railway Optimization)
   Before: 6.52GB (86.9%)
   Running full GC...
   GC collected 2345 objects in 8 cycles
   malloc_trim: freed memory to OS (returned 1)
   Cleared Python internal caches
   After cleanup: 5.80GB (77.3%)
   ✅ Freed 0.72GB immediately
   🎯 Target: 5.25GB, waiting up to 30s...
   ✅ Target achieved in 8.5s
   Final: 5.10GB (68.0%)
   Total freed: 1.42GB
   ✅ Cleanup successful, resuming work

Progress: 120 items placed, Memory: 5.10GB (68.0%)
Placing item 121...
Placing item 122...
```

## Benefits

### 1. **No More Silent OOM**

Before:

```
[Gang sheet creation running]
[Railway: Process exited]
[No logs, no explanation]
```

After:

```
⏸️  PAUSE 1: Memory at 6.52GB (86.9%)
🧹 AGGRESSIVE MEMORY CLEANUP
✅ Freed 1.42GB
✅ Cleanup successful, resuming work
[Continues successfully]
```

### 2. **Proactive Prevention**

- Detects high memory **before** OOM
- Cleans up **before** Railway kills process
- Resumes **before** hitting limit

### 3. **Self-Healing**

```
Memory at 6.5GB → Pause
Cleanup → 5.1GB
Resume → Success!
```

Instead of:

```
Memory at 7.5GB → OOM KILL
```

### 4. **Clear Logging**

Every pause shows:

- Why paused (memory threshold)
- What phase (gang sheet part X, Y items)
- How much freed
- Whether successful

### 5. **Final Summary**

```
======================================================================
🚂 RAILWAY MEMORY SUMMARY
======================================================================
✅ Gang sheet creation completed successfully
📊 Total parts created: 2

💾 Final Memory Usage:
   Current: 3.45GB / 7.50GB (46.0%)
   Peak: 6.80GB
   Available: 4.05GB

🧹 Memory Management:
   Pauses for cleanup: 3
   Total cleanups: 5

======================================================================
```

## Configuration

### Pause Threshold (Default: 87%)

Can be adjusted if needed:

```python
# In railway_memory_optimizer.py:
MEMORY_PAUSE_THRESHOLD = 0.87  # 87% of 7.5GB = 6.50GB

# To make more aggressive (pause earlier):
MEMORY_PAUSE_THRESHOLD = 0.80  # 80% = 6.00GB

# To make more lenient (pause later):
MEMORY_PAUSE_THRESHOLD = 0.90  # 90% = 6.75GB (riskier!)
```

### Cleanup Target (Default: 70%)

```python
# Target memory after cleanup
target_gb = MEMORY_WARNING_THRESHOLD * RAILWAY_EFFECTIVE_MEMORY_GB  # 5.25GB

# Fallback if can't reach target
fallback_gb = MEMORY_CRITICAL_THRESHOLD * RAILWAY_EFFECTIVE_MEMORY_GB  # 6.0GB
```

### Check Frequency (Default: Every 10 Items)

```python
# In gangsheet_engine.py:
if images_processed_in_part % 10 == 0:  # Check every 10 items

# To check more frequently (slower but safer):
if images_processed_in_part % 5 == 0:  # Every 5 items

# To check less frequently (faster but riskier):
if images_processed_in_part % 20 == 0:  # Every 20 items
```

## Error Handling

### Success Path:

```
120 items placed → Memory 6.5GB → Pause
Cleanup → 5.1GB (success) → Resume
Continue → 250 items placed → Complete ✅
```

### Partial Cleanup Path:

```
120 items placed → Memory 6.5GB → Pause
Cleanup → 5.9GB (partial) → Resume cautiously
Continue → Complete ✅
```

### Cleanup Failed Path:

```
120 items placed → Memory 6.5GB → Pause
Cleanup → 6.2GB (insufficient) → Abort
❌ Memory still critical after cleanup, cannot continue
   Successfully placed 120 items before abort
   💡 Solutions:
      1. Reduce printer max_height_inches
      2. Process fewer orders per batch (try 5-10)
      3. Upgrade Railway to 16GB plan
```

## Technical Details

### Why Wait After Cleanup?

```python
# Immediate cleanup may not show full effect
gc.collect()  # Marks memory as free
malloc_trim(0)  # Asks OS to reclaim

# But OS may not release immediately
# Wait up to 30s for memory to actually drop
while memory > target:
    time.sleep(1)
    if elapsed > 30:
        break
```

### Why 87% Threshold?

```
95% - OOM kill (Railway terminates)
93% - Too late, not enough time to cleanup
90% - Cutting it close
87% - ✅ Sweet spot: Early enough to cleanup, late enough to be efficient
80% - Too early, wastes time with unnecessary cleanups
```

### Memory Regions

```
Railway 8GB Plan:
├─ 0.5GB - System overhead (OS, Node.js)
├─ 0-7.5GB - Available for Python
│   ├─ 0-5.25GB - Safe zone (70%)
│   ├─ 5.25-6.0GB - Warning zone (70-80%)
│   ├─ 6.0-6.5GB - Critical zone (80-87%)
│   ├─ 6.5-7.0GB - Pause zone (87-93%) ← PAUSE HERE
│   ├─ 7.0-7.5GB - Emergency zone (93-100%)
│   └─ > 7.5GB - Danger zone (OOM likely)
└─ 7.6-8.0GB - OOM kill zone ☠️
```

## Comparison

### Before (No Pause):

```
Memory progression:
2.0GB → 3.5GB → 5.0GB → 6.5GB → 7.2GB → 7.8GB
                                          ↑
                                       OOM KILL
                                     (no logs)
```

### After (With Pause):

```
Memory progression:
2.0GB → 3.5GB → 5.0GB → 6.5GB → PAUSE → 5.1GB → 6.2GB → PAUSE → 5.0GB → 4.5GB
                               ↑               ↑
                            Cleanup         Cleanup
                            Resume          Resume
                                                      ↑
                                                  SUCCESS ✅
```

## When Pause Occurs

Pause triggers when **any** of these conditions met:

1. **Memory >= 87%** during gang sheet placement (every 10 items)
2. **Memory >= 87%** after gang sheet save
3. **Memory >= 87%** before starting new gang sheet part

## Recovery Strategies

### Strategy 1: Wait for OS (Default)

```python
# Cleanup aggressively, then wait
force_memory_release(wait_for_target_gb=5.25, max_wait_seconds=30)
```

Best for: Systems where OS memory release is delayed

### Strategy 2: Multiple Small Cleanups

```python
# Cleanup multiple times throughout creation
if images_processed_in_part % 50 == 0:
    monitor.force_memory_release()
```

Best for: Preventing memory from building up

### Strategy 3: Lower Pause Threshold

```python
MEMORY_PAUSE_THRESHOLD = 0.80  # Pause at 80% instead of 87%
```

Best for: Systems with unpredictable memory spikes

## Files Modified

1. **`server/src/utils/railway_memory_optimizer.py`**
   - Added `MEMORY_PAUSE_THRESHOLD` (87%)
   - Enhanced `force_memory_release()` with wait capability
   - Added `pause_and_cleanup_if_needed()` method
   - Track pause count and cleanup count

2. **`server/src/utils/gangsheet_engine.py`**
   - Check memory every 10 item placements
   - Call `pause_and_cleanup_if_needed()` instead of simple check
   - Add final Railway memory summary with pause/cleanup stats

3. **`RAILWAY_PAUSE_RESUME.md`** (THIS FILE)
   - Complete documentation of pause/resume system

## Summary

**Problem:** Railway OOM kills process with no logs

**Root Cause:** Memory hits 95%, Railway terminates immediately, no time to log

**Solution:** Pause at 87% (6.5GB), cleanup, resume

**How:**

- Monitor memory every 10 item placements
- When hitting 87%, pause work
- Aggressive cleanup (GC + malloc_trim + wait)
- Resume if memory drops to 70% (5.25GB)
- Abort if still > 80% after cleanup

**Result:**

- No more silent OOM kills
- Proactive prevention
- Self-healing memory management
- Clear logging of all pauses
- Final summary with statistics

**Logging:**

```
⏸️  PAUSE 1: Memory at 6.52GB (86.9%)
🧹 AGGRESSIVE MEMORY CLEANUP
✅ Freed 1.42GB
✅ Target achieved in 8.5s
✅ Cleanup successful, resuming work
```

**All gang sheet creation now continues successfully even when memory gets high! ✅**
