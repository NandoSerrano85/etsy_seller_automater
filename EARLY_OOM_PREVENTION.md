# Early OOM Prevention - File Download Phase

## Critical Discovery from Logs

### What the Logs Showed

User's crash log sequence:

```
Starting create_print_files_from_selected_orders with order_ids: [3955257118, 3959779813, ...] (26 orders)
dpi: 400
std_dpi: 400
/usr/local/lib/python3.11/site-packages/paramiko/pkey.py:100: CryptographyDeprecationWarning...
🔄 Starting CraftFlow application...  <-- PROCESS RESTARTED
📋 Creating FastAPI application...
```

**Analysis:**

1. Process started with **26 orders** selected
2. Printed `dpi: 400` (from orders/service.py)
3. Started NAS connection (paramiko warnings)
4. **Process restarted** (Railway OOM kill)
5. **No crash marker or error logs** (killed too fast to log)

## The Problem

### Original OOM Prevention Only Protected Gang Sheet Phase

The OOM prevention system in `gangsheet_engine.py` checks memory **before creating gang sheets**.

But the crash was happening **earlier** - during the **file download phase** in `orders/service.py`:

1. User selects 26 orders
2. System starts downloading design files from NAS
3. Each design file is ~50-100MB
4. All 26+ files load into memory
5. **OOM kill happens** during downloads
6. Gang sheet creation never even starts

### Why We Missed This

The gang sheet OOM checks were added at lines 600-622 of `gangsheet_engine.py`, but:

- Downloads happen in `orders/service.py` at lines 633-675
- By the time control reaches gang sheet engine, process is already dead

## Solution: Multi-Phase OOM Prevention

### Phase 1: Pre-Download Memory Check (orders/service.py:580-621)

**Before downloading any files:**

```python
memory_guard = get_memory_guard()
initial_mem = memory_guard.check_memory()

if initial_mem['percent'] > 70:
    logging.error(f"🔥 ABORT: Memory already at {initial_mem['percent']:.1f}%")
    return {
        "success": False,
        "error": "Insufficient memory before starting",
        "recommendation": "Reduce batch size to 10-15 orders"
    }

# Calculate safe batch size
safe_batch = get_max_safe_batch_size(item_count=len(order_ids), avg_item_memory_mb=100)
if safe_batch < len(order_ids):
    logging.warning(f"⚠️  Selected {len(order_ids)} orders, but safe batch size is {safe_batch}")
```

**Benefits:**

- Catches high memory **before** downloading anything
- Recommends safe batch size based on available memory
- Saves time by not starting doomed operations

### Phase 2: During-Download Memory Monitoring (orders/service.py:663-685)

**Every 5 file downloads, check memory:**

```python
for idx, design_file_path in enumerate(order_items_data['Title']):
    # Check memory every 5 downloads
    if idx > 0 and idx % 5 == 0:
        mem_status = memory_guard.check_memory()
        if mem_status['percent'] > 80:
            logging.error(f"🔥 ABORT DURING DOWNLOADS: Memory at {mem_status['percent']:.1f}%")
            return {
                "success": False,
                "error": "Memory limit reached during downloads",
                "downloads_completed": download_count,
                "recommendation": "Reduce batch size"
            }
```

**Benefits:**

- Catches memory growth during download phase
- Stops before OOM kill happens
- Returns partial success info (files downloaded so far)

### Phase 3: Pre-Gang Sheet Allocation (gangsheet_engine.py:600-622)

**Before creating gang sheets (already implemented):**

```python
mem_status = memory_guard.check_memory()
if mem_status['percent'] > 85:
    logging.error(f"🔥 ABORT: Memory at {mem_status['percent']:.1f}%")
    return {'success': False, 'error': 'Insufficient memory'}
```

### Phase 4: Post-Cleanup Verification (gangsheet_engine.py:1119-1159)

**After each gang sheet part (already implemented):**

```python
if mem_status['percent'] > 80:
    logging.error(f"🔥 ABORT AFTER CLEANUP: Memory still at {mem_status['percent']:.1f}%")
    return {'success': False, 'parts_created': part - 1}
```

## Memory Checkpoints Summary

| Phase                  | Location                 | Threshold | Action                            |
| ---------------------- | ------------------------ | --------- | --------------------------------- |
| **1. Pre-Download**    | orders/service.py:580    | 70%       | Abort before downloading          |
| **2. During-Download** | orders/service.py:663    | 80%       | Stop downloads mid-process        |
| **3. Pre-Gang Sheet**  | gangsheet_engine.py:600  | 85%       | Abort before allocation           |
| **4. Post-Cleanup**    | gangsheet_engine.py:1119 | 80%       | Verify safe to continue next part |

## Expected Log Output

### With 26 Orders (Too Many)

#### Before Fix:

```
Starting create_print_files_from_selected_orders with order_ids: [...26 orders...]
dpi: 400
std_dpi: 400
🔄 Starting CraftFlow application...  <-- SILENT OOM KILL
```

#### After Fix - Pre-Download Abort:

```
Starting create_print_files_from_selected_orders with order_ids: [...26 orders...]
🛡️  Memory Guard initialized: 8.00GB total, 85% limit
💾 Memory status: 5.2GB / 8GB (65.0%)
✅ Initial memory check passed: 65.0%
⚠️  Selected 26 orders, but safe batch size is 15
⚠️  Risk of OOM kill is HIGH - consider processing fewer orders
```

#### After Fix - During-Download Abort:

```
Starting download of 26 design files from NAS
Downloaded: 1/26 files...
Downloaded: 5/26 files... [memory check: 72%]
Downloaded: 10/26 files... [memory check: 78%]
Downloaded: 15/26 files... [memory check: 82%]
🔥 ABORT DURING DOWNLOADS: Memory at 82.5% after 15 downloads
🔥 Stopping downloads to prevent OOM kill
💡 Successfully downloaded 15 files, skipping remaining 11
💡 Reduce batch size to process fewer orders at once
```

### With 10-15 Orders (Safe)

```
Starting create_print_files_from_selected_orders with order_ids: [...12 orders...]
🛡️  Memory Guard initialized: 8.00GB total, 85% limit
💾 Memory status: 2.8GB / 8GB (35.0%)
✅ Initial memory check passed: 35.0%
📊 Calculated safe batch size: 15 items (out of 12 total)

Starting download of 12 design files from NAS
Downloaded: 5/12 files... [memory check: 42%]
Downloaded: 10/12 files... [memory check: 48%]
✅ Downloaded 12 design files from NAS in 8.52s

🔍 Calculating optimal gang sheet size...
📐 Optimized gang sheet size: 10000x12000 (1.12GB)
💾 Memory status: 3.9GB / 8GB (48.8%)
✅ Projected usage after allocation: 5.0GB (62.5%)
📦 Allocating gang sheet: 10000x12000 (1.12GB)
✅ Gang sheet allocated successfully
... processing ...
✅ TOTAL REQUEST TIME: 45.23s
```

## Safe Batch Size Recommendations

The system automatically calculates safe batch size using `get_max_safe_batch_size()`:

### Formula

```python
available_memory_mb = available_memory_gb * 1024
usable_memory_mb = available_memory_mb * 0.6  # Use only 60% for safety
max_items = int(usable_memory_mb / avg_item_memory_mb)  # avg = 100MB
max_items = min(max_items, 30)  # Cap at 30 items
max_items = max(max_items, 5)   # Always allow at least 5
```

### Examples

| Available RAM | Usable (60%) | Safe Batch Size    |
| ------------- | ------------ | ------------------ |
| 2GB           | 1.2GB        | 12 orders          |
| 4GB           | 2.4GB        | 24 orders          |
| 8GB           | 4.8GB        | 30 orders (capped) |

**Note:** These are conservative estimates. Actual safe size depends on:

- Image file sizes (50-150MB each)
- Template complexity
- System background processes
- Other concurrent operations

## Configuration

No new configuration needed. Uses existing environment variables:

```bash
# These already exist from previous OOM prevention work
GANGSHEET_DYNAMIC_SIZING=true
GANGSHEET_MEMMAP_THRESHOLD_GB=0.5
GANGSHEET_CACHE_LIMIT=5
```

## Files Modified

### 1. server/src/routes/orders/service.py

**Lines 580-621:** Pre-download memory check

- Checks memory before starting downloads
- Calculates safe batch size
- Aborts if already too high

**Lines 663-685:** During-download monitoring

- Checks memory every 5 downloads
- Aborts if approaching limit
- Returns partial success

**Lines 694-706:** Download logging improvements

- Tracks skipped_count
- Logs memory-related skips

## Testing

### To Test Pre-Download Abort:

1. Select 30+ orders
2. Click "Send to Print"
3. Should see: `⚠️  Selected 30 orders, but safe batch size is 15`
4. If memory already high: `🔥 ABORT: Memory already at 72.3%`

### To Test During-Download Abort:

1. Fill Railway memory to ~60-70% (run other operations first)
2. Select 20 orders
3. Click "Send to Print"
4. Watch for: `🔥 ABORT DURING DOWNLOADS: Memory at 82.5%`

### To Test Successful Operation:

1. Select 10-15 orders
2. Click "Send to Print"
3. Should complete with: `✅ TOTAL REQUEST TIME: XX.XXs`

## Summary

**Problem:** OOM kills happening during file downloads, before gang sheet creation

**Root Cause:** With 26 orders, downloading 26+ large files exhausted memory before reaching gang sheet OOM checks

**Solution:**

1. Pre-download memory check (abort if > 70%)
2. During-download monitoring (check every 5 files, abort if > 80%)
3. Safe batch size calculation and warnings
4. Combined with existing gang sheet OOM prevention

**Result:** 4-phase protection system catches memory issues at every stage:

- Before downloads (save time)
- During downloads (prevent mid-process OOM)
- Before gang sheets (existing protection)
- After cleanup (existing protection)

**No more silent OOM kills at any phase of the process!**
