# OOM Kill Prevention System - Complete Implementation

## Problem Solved

**Issue:** Railway was hitting the 8GB memory threshold and performing **OOM (Out of Memory) kills** - instantly terminating the process with **no error logs**.

When Railway's memory usage reaches ~95%, the system immediately kills the process. This happens so fast that the application doesn't get a chance to log any errors, making debugging extremely difficult.

## Solution Implemented

A comprehensive **proactive memory monitoring system** that prevents the process from ever reaching the OOM kill threshold.

### Key Components

#### 1. Memory Emergency Module (`memory_emergency.py`)

Created a dedicated utility module with:

- **MemoryGuard Class**: Monitors memory usage and prevents dangerous allocations
- **Proactive Checking**: Tests if allocation is safe BEFORE attempting it
- **Emergency Cleanup**: Aggressive garbage collection when needed
- **Railway-Specific Thresholds**: Set at 85% to stop before Railway kills at 95%

```python
class MemoryGuard:
    def __init__(self, max_memory_percent: float = 85.0):
        """Railway OOM kills at ~95%, so we stop at 85% for safety"""

    def can_allocate(self, size_gb: float) -> tuple[bool, str]:
        """Check if we can safely allocate size_gb without OOM kill"""
        projected_percent = (current_gb + size_gb) / total_gb * 100

        if projected_percent > self.max_memory_percent:
            return False, f"Would reach {projected_percent:.1f}%"

        return True, "safe"
```

#### 2. Pre-Allocation Memory Checks (`gangsheet_engine.py:600-622`)

**Before creating each gang sheet:**

1. Check current memory usage
2. If > 85%, **abort immediately** before allocation
3. Provide actionable recommendations to user
4. Return partial success with parts already created

```python
mem_status = memory_guard.check_memory()

if mem_status['percent'] > 85:
    logging.error(f"🔥 ABORT: Memory at {mem_status['percent']:.1f}%")
    logging.error(f"🔥 This would cause OOM kill. Stopping to prevent crash.")
    return {
        'success': False,
        'error': f'Insufficient memory: {mem_status["percent"]:.1f}% usage',
        'parts_created': part - 1,
        'recommendation': 'Reduce batch size or upgrade Railway plan'
    }
```

#### 3. Pre-Allocation Garbage Collection (`gangsheet_engine.py:625-636`)

**Before allocating gang sheet memory:**

1. Force 3 cycles of aggressive garbage collection
2. Check memory again after GC
3. Log memory freed by GC

This ensures any lingering objects from previous iterations are cleaned up before attempting allocation.

#### 4. Post-Cleanup Memory Verification (`gangsheet_engine.py:1119-1159`)

**After cleaning up each gang sheet part:**

1. Check if there are more parts to create
2. Verify memory is low enough to proceed (< 80%)
3. If still too high, abort and return partial success
4. Prevents starting next iteration if cleanup didn't free enough memory

```python
# Check memory after cleanup but before next iteration
if len(visited) > 0 and sum(visited.values()) > 0:
    mem_status = memory_guard.check_memory()

    if mem_status['percent'] > 80:
        logging.error(f"🔥 ABORT AFTER CLEANUP: Memory still at {mem_status['percent']:.1f}%")
        logging.error(f"🔥 Not enough memory freed to continue")
        return {
            'success': False,
            'error': f'Insufficient memory after part {part-1}',
            'parts_created': part - 1
        }
```

## How It Works

### Memory Check Points

The system now has **3 critical checkpoints**:

1. **Before Allocation** (lines 600-622)
   - Checks if we have room for the gang sheet
   - Aborts if memory > 85%

2. **After GC, Before Allocation** (lines 625-636)
   - Runs aggressive garbage collection
   - Verifies GC freed enough memory
   - Logs memory status

3. **After Cleanup, Before Next Iteration** (lines 1119-1159)
   - Verifies cleanup actually freed memory
   - Checks if safe to continue with next part
   - Aborts if still too high after cleanup

### Safety Margins

- **Railway OOM Kill Threshold**: ~95% memory usage
- **Our Abort Threshold**: 85% memory usage (before allocation)
- **Our Warning Threshold**: 70% memory usage
- **Post-Cleanup Abort Threshold**: 80% memory usage

This gives us a **10-15% safety margin** to prevent OOM kills.

## Expected Behavior

### Normal Operation (Enough Memory)

```
🔍 Calculating optimal gang sheet size...
📐 Optimized gang sheet size: 10000x12000 (1.12GB)
💾 Memory status: 2.5GB / 8GB (31.2%)
📦 Allocating gang sheet: 10000x12000 (1.12GB)
✅ Gang sheet allocated successfully

... processing ...

🧹 CLEANUP: Starting cleanup for part 1
✅ CLEANUP COMPLETE: Freed 1.5GB
PART 1 COMPLETE: Using 1.2GB, 6.8GB available for next part
✅ Memory check passed: 35.1% - safe to continue

🔄 LOOP: Continuing to next part. Remaining items: 15
```

### Memory Limit Reached (Before Allocation)

```
💾 Memory status: 6.9GB / 8GB (86.3%)
🔥 ABORT: Memory at 86.3% - refusing to allocate gang sheet
🔥 This would cause OOM kill. Stopping to prevent crash.
💡 Solutions:
   1. Enable aggressive optimizations: GANGSHEET_MEMMAP_THRESHOLD_GB=0.2
   2. Process fewer orders per batch (select 10-15 orders instead)
   3. Upgrade Railway to Pro plan (32GB RAM)

✅ Successfully created 1 gang sheet parts before running out of memory
```

### Memory Limit Reached (After Cleanup)

```
🧹 CLEANUP: Starting cleanup for part 2
✅ CLEANUP COMPLETE: Freed 1.2GB
PART 2 COMPLETE: Using 6.6GB, 1.4GB available for next part
🔥 ABORT AFTER CLEANUP: Memory still at 82.5%
🔥 Not enough memory freed to continue with next gang sheet
💡 Solutions:
   1. Process fewer orders per batch (currently processing 10 remaining items)
   2. Enable more aggressive optimizations: GANGSHEET_MEMMAP_THRESHOLD_GB=0.2
   3. Upgrade Railway to Pro plan (32GB RAM)

✅ Successfully created 2 gang sheet parts before running out of memory
```

## Benefits

### 1. No More Silent OOM Kills

- Process stops gracefully before Railway kills it
- Always get error logs explaining why it stopped
- User gets actionable recommendations

### 2. Partial Success Handling

- Creates as many gang sheet parts as memory allows
- Returns success info about parts created
- User can process fewer orders and try again

### 3. Clear Error Messages

- Logs show exact memory percentage
- Explains why it stopped (memory limit)
- Provides 3 concrete solutions

### 4. Proactive Prevention

- Checks memory BEFORE allocation (not after crash)
- Multiple checkpoints throughout process
- Aggressive cleanup between parts

## Configuration

### Environment Variables

All existing memory optimizations still apply:

```bash
# Dynamic sizing (30-70% savings)
GANGSHEET_DYNAMIC_SIZING=true

# Memory-mapped files threshold
GANGSHEET_MEMMAP_THRESHOLD_GB=0.5  # or 0.3 for more aggressive

# Image cache limit
GANGSHEET_CACHE_LIMIT=5  # or 3 for more aggressive
```

### Railway Plans

| Plan  | RAM   | Recommended For                          |
| ----- | ----- | ---------------------------------------- |
| Free  | 512MB | ❌ Not enough for gang sheets            |
| Hobby | 8GB   | ✅ Works with optimizations + monitoring |
| Pro   | 32GB  | ✅ No memory issues                      |

With the OOM prevention system, the **Hobby plan ($5/mo)** should work reliably for most workloads.

## Testing

### To Test OOM Prevention:

1. Deploy the updated code to Railway
2. Select a large batch of orders (20-30 items)
3. Click "Send to Print"
4. Watch Railway logs for emoji markers:
   - 🛡️ Memory Guard initialized
   - 💾 Memory status checks
   - 🔥 Abort messages (if memory limit hit)
   - ✅ Memory check passed

### Expected Results:

- **Small batches (10-15 orders)**: Should complete all parts successfully
- **Large batches (30+ orders)**: May hit memory limit and stop gracefully with partial success
- **No OOM kills**: Railway should never kill the process - it stops itself first

## Files Modified

1. **server/src/utils/memory_emergency.py** (created)
   - MemoryGuard class
   - Helper functions for memory monitoring

2. **server/src/utils/gangsheet_engine.py** (updated)
   - Pre-allocation memory check (lines 600-622)
   - Pre-allocation GC (lines 625-636)
   - Post-cleanup memory check (lines 1119-1159)

## Summary

**Before:**

- Railway OOM kills at 95% with no logs
- User had no idea why it crashed
- Lost all work on multi-part gang sheets

**After:**

- Process stops itself at 85% before OOM kill
- Clear error logs with memory percentage
- Returns partial success with parts created
- Provides actionable recommendations
- User can adjust batch size and retry

**Result:** Multi-part gang sheets will either complete successfully or stop gracefully with helpful error messages - **no more silent OOM kills!**
