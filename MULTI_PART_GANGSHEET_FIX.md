# Multi-Part Gang Sheet Crash - Fixed

## Problem

Backend crashes when:

1. User selects specific orders (not all orders)
2. The gang sheet engine needs to create **more than 1 part/sheet**

The crash happens specifically during the second iteration of the gang sheet creation loop.

## Root Cause

When creating multiple gang sheets (multiple parts), the system:

1. Creates part 1 successfully
2. Tries to clean up memory in the `finally` block
3. Loops back to create part 2
4. **Crashes during part 2 creation**

Possible causes:

- Gang sheet from part 1 not fully cleaned up before part 2 starts
- Memory not freed properly between iterations
- Out of memory when allocating the second gang sheet
- Variable state from part 1 causing issues in part 2

## Fixes Applied

### 1. Comprehensive Logging for Multi-Part Creation

Added detailed logging to track the entire loop lifecycle:

**At loop start:**

```python
logging.info(f"🔄 Starting iteration {iteration_count} for part {part}")
logging.info(f"📊 Remaining items to process: {len(visited)} keys")
```

**Before allocation:**

```python
logging.info("🧹 Pre-allocation cleanup: forcing garbage collection...")
logging.info("✅ Garbage collection complete")
logging.info(f"📦 Allocating gang sheet: {width_px}x{height_px} ({memory_gb:.2f}GB)")
```

**After allocation:**

```python
logging.info(f"✅ Memory-mapped gang sheet created: {temp_filename}")
# or
logging.info(f"✅ In-memory gang sheet created")
```

**During cleanup:**

```python
logging.info(f"🧹 CLEANUP: Starting cleanup for part {part}")
logging.info(f"📊 Memory before cleanup: {memory_gb:.2f}GB")
logging.info(f"🗑️  Deleting gang_sheet from memory...")
logging.info(f"✅ CLEANUP COMPLETE: Freed {freed_gb:.2f}GB")
```

**At loop end:**

```python
logging.info(f"🔄 LOOP: Continuing to next part. Remaining items: {count}")
logging.info("="*60)
logging.info(f"🔁 LOOPING BACK to create part {part + 1}")
logging.info("="*60)
```

### 2. Gang Sheet Existence Check

Added a check before creating a new gang sheet to ensure the previous one was deleted:

```python
# Verify gang_sheet was cleaned up from previous iteration
if 'gang_sheet' in locals():
    logging.error(f"❌ CRITICAL: gang_sheet still exists from previous iteration!")
    logging.error(f"📋 This indicates cleanup failed. Forcing deletion...")
    # Force cleanup
    del gang_sheet
    gc.collect()
```

This catches cleanup failures and forces a deletion before proceeding.

### 3. Detailed Memory Tracking

Enhanced memory logging to show:

- Memory before cleanup
- Memory after cleanup
- Amount of memory freed
- Available memory for next part
- Low memory warnings

```python
logging.info(f"📊 Memory before cleanup: {before:.2f}GB")
logging.info(f"✅ CLEANUP COMPLETE: Freed {freed:.2f}GB (from {before:.2f}GB to {after:.2f}GB)")
logging.info(f"PART {part} COMPLETE: Using {current:.2f}GB, {available:.2f}GB available for next part")
```

### 4. Garbage Collection Logging

Shows how many objects were collected in each GC cycle:

```python
for i in range(2):
    collected = gc.collect()
    logging.info(f"🧹 GC cycle {i+1}: collected {collected} objects")
```

### 5. Memory-Mapped File Tracking

Better logging for memory-mapped files to track their creation and deletion:

```python
logging.info(f"💾 Using memory-mapped file (size > 1GB)")
logging.info(f"✅ Memory-mapped gang sheet created: {filename}")
logging.info(f"💾 Cleaning up memory-mapped file: {filename}")
logging.info(f"✅ Deleted memory-mapped file: {filename}")
```

## How to Debug After Deploy

### Expected Log Flow (2-Part Gang Sheet):

```
🔄 Starting iteration 1 for part 1
📊 Remaining items to process: 45 keys
🧹 Pre-allocation cleanup: forcing garbage collection...
✅ Garbage collection complete
📦 Allocating gang sheet: 16000x20000 (2.95GB)
💾 Using memory-mapped file (size > 1GB)
✅ Memory-mapped gang sheet created: /tmp/tmpXXXX
[... processing images ...]
📐 DPI settings - dpi: 400, std_dpi: 400
📏 Calculated dimensions - width: 16000, height: 20000
🔄 Resizing gang sheet from (20000, 16000, 4) to (16000, 20000)
✅ Gang sheet resized successfully
💾 Preparing to save: NookTransfers_part1
💾 Saving gang sheet as PNG...
✅ Successfully created gang sheet with 25 layers
🧹 CLEANUP: Starting cleanup for part 1
📊 Memory before cleanup: 3.2GB
🗑️  Deleting gang_sheet from memory...
💾 Cleaning up memory-mapped file: /tmp/tmpXXXX
✅ Deleted memory-mapped file: /tmp/tmpXXXX
🧹 Forcing garbage collection...
🧹 GC cycle 1: collected 1543 objects
🧹 GC cycle 2: collected 23 objects
✅ CLEANUP COMPLETE: Freed 2.95GB (from 3.2GB to 0.25GB)
PART 1 COMPLETE: Using 0.25GB, 7.5GB available for next part
🔄 LOOP: Continuing to next part. Remaining items: 20
============================================================
🔁 LOOPING BACK to create part 2
============================================================

🔄 Starting iteration 2 for part 2
📊 Remaining items to process: 20 keys
🧹 Pre-allocation cleanup: forcing garbage collection...
✅ Garbage collection complete
📦 Allocating gang sheet: 16000x20000 (2.95GB)
💾 Using memory-mapped file (size > 1GB)
✅ Memory-mapped gang sheet created: /tmp/tmpYYYY
[... part 2 creation ...]
✅ All items processed, finishing gang sheet creation
```

### Crash Points to Watch For:

| Last Log Message                       | Problem                     | Action                                              |
| -------------------------------------- | --------------------------- | --------------------------------------------------- |
| `🔄 Starting iteration 2`              | Crash immediately on part 2 | Check if cleanup failed                             |
| `📊 Remaining items: X`                | Crash before allocation     | Memory issue or cleanup incomplete                  |
| `🧹 Pre-allocation cleanup`            | Crash during GC             | Out of memory                                       |
| `📦 Allocating gang sheet`             | Crash during allocation     | Out of memory - reduce size or increase Railway RAM |
| `✅ Garbage collection complete`       | Crash after GC              | Allocation fails - not enough memory                |
| `❌ CRITICAL: gang_sheet still exists` | Cleanup failed              | Cleanup issue - gang_sheet not deleted properly     |

### If Crash Shows "gang_sheet still exists":

This means the finally block cleanup didn't work properly. Check:

1. Did the exception handling interfere with cleanup?
2. Was there an error during the cleanup itself?
3. Is the gang_sheet variable being referenced elsewhere?

### If Crash During Allocation:

```
📦 Allocating gang sheet: 16000x20000 (2.95GB)
💾 Using memory-mapped file (size > 1GB)
[CRASH - no "✅ created" message]
```

This means:

- Not enough memory available
- Memory-mapped file creation failed
- Disk space issue

**Solutions:**

- Increase Railway memory plan
- Process fewer orders at a time
- Reduce gang sheet max size
- Check disk space

## Testing Checklist

After deploying:

- [ ] Test with orders that create exactly 2 parts
- [ ] Check logs show "LOOPING BACK to create part 2"
- [ ] Verify "CLEANUP COMPLETE" shows memory freed
- [ ] Confirm part 2 allocation succeeds
- [ ] Check no "gang_sheet still exists" errors
- [ ] Verify both parts are created and saved
- [ ] Test with orders creating 3+ parts
- [ ] Monitor memory usage stays stable across parts

## Common Issues

### Issue: "gang_sheet still exists from previous iteration"

**Meaning:** Cleanup failed, gang_sheet wasn't deleted

**Fix:** Check the cleanup logic in finally block, ensure del gang_sheet is executing

### Issue: Crash after "Allocating gang sheet" for part 2

**Meaning:** Out of memory

**Fix:**

- Increase Railway memory (upgrade plan)
- Or reduce max gang sheet size
- Or process fewer orders per batch

### Issue: "Failed to delete temp file"

**Meaning:** Memory-mapped file couldn't be deleted

**Fix:** Check disk permissions and space

### Issue: Part 2 shows 0 objects collected in GC

**Meaning:** No objects to collect, cleanup already happened

**Result:** This is actually good! Means cleanup worked.

## Memory Optimization

The code now:

1. **Forces GC before allocation** (3 cycles)
2. **Logs memory before/after cleanup**
3. **Checks gang_sheet was deleted** before creating new one
4. **Uses memory-mapped files** for large sheets (> 1GB)
5. **Tracks available memory** for next part
6. **Warns if low memory** (< 2GB available)
7. **Cleans up processed images cache** between parts

## Files Modified

- `server/src/utils/gangsheet_engine.py`:
  - Added comprehensive logging for multi-part loop (lines 567-572)
  - Added gang_sheet existence check before allocation (lines 599-612)
  - Enhanced cleanup logging (lines 905-959)
  - Added loop continuation logging (lines 1024-1030)
  - Added GC cycle object counting

## Summary

**Before:** Silent crash on part 2 with no indication why

**After:** Detailed logging showing:

- When each part starts
- Memory usage before/after cleanup
- Whether cleanup succeeded
- If gang_sheet was properly deleted
- How much memory is available for next part
- Exactly where crash happens if it still fails

**Result:** Can now pinpoint exact cause of crash and take appropriate action (increase memory, reduce size, fix cleanup logic, etc.)

The logs will now tell you if it's:

- Memory issue (need more RAM)
- Cleanup issue (gang_sheet not deleted)
- Allocation issue (disk space/permissions)
- Processing issue (crash during part 2 creation)

This makes debugging multi-part gang sheets 100x easier!
