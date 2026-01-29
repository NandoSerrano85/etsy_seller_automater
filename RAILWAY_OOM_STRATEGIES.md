# Additional Railway OOM Prevention Strategies

Beyond the fixes already applied (8GB detection, pause/resume), here are more aggressive strategies for Railway's memory constraints:

## Strategy 1: Auto-Split Large Batches ⭐⭐⭐ (RECOMMENDED)

**What:** Automatically split large order batches into smaller sub-batches
**Impact:** Most effective - prevents large memory spikes
**Complexity:** Medium (new file created, needs integration)

### Implementation

**File Created:** `server/src/utils/memory_aware_batch_splitter.py`

**How It Works:**

```python
# Before (1 batch of 50 items = 1 huge gang sheet = OOM)
50 items → 1 gang sheet (6GB) → OOM

# After (split into 4 batches = 4 smaller gang sheets)
15 items → Gang sheet 1 (1.8GB) → Success
15 items → Gang sheet 2 (1.8GB) → Success
15 items → Gang sheet 3 (1.8GB) → Success
5 items  → Gang sheet 4 (0.6GB) → Success
```

**Benefits:**

- Smaller gang sheets use less memory
- Cleanup between batches
- Each batch independent (if one fails, others succeed)
- Automatic - no user action needed

**Configuration:**

```python
# In memory_aware_batch_splitter.py:
max_items_per_batch = 15  # Reduce to 10 for more safety
max_memory_per_batch_gb = 2.0  # Target max gang sheet size
```

### Integration into orders/service.py

Add before gang sheet creation:

```python
from server.src.utils.memory_aware_batch_splitter import process_with_memory_aware_splitting

# Replace this:
result = create_gang_sheets(
    image_data=order_items_data,
    ...
)

# With this:
result = process_with_memory_aware_splitting(
    order_items_data=order_items_data,
    create_gang_sheets_func=create_gang_sheets,
    image_type=template_name,
    output_path=output_dir,
    total_images=len(order_items_data.get('Title', [])),
    max_width_inches=gang_sheet_max_width,
    max_height_inches=gang_sheet_max_height,
    dpi=gang_sheet_dpi,
    std_dpi=gang_sheet_dpi,
    file_format=format
)
```

**Expected Logs:**

```
📊 Batch analysis:
   Total items: 45
   Unique designs: 38
   Estimated gang sheet: 4.2GB
⚠️  Batch too large, will split:
   - 38 unique items > 15 max
   - 4.2GB estimated > 2.5GB max

======================================================================
🔄 MEMORY-AWARE BATCH SPLITTING ACTIVE
======================================================================
📦 Splitting 45 items into 3 sub-batches of ~15 items

======================================================================
📦 PROCESSING SUB-BATCH 1/3
======================================================================
Items in this sub-batch: 15
✅ Sub-batch 1 complete: 1 gang sheets created

======================================================================
📦 PROCESSING SUB-BATCH 2/3
======================================================================
Items in this sub-batch: 15
✅ Sub-batch 2 complete: 1 gang sheets created

======================================================================
📦 PROCESSING SUB-BATCH 3/3
======================================================================
Items in this sub-batch: 15
✅ Sub-batch 3 complete: 1 gang sheets created

======================================================================
✅ ALL SUB-BATCHES COMPLETE
======================================================================
Total sub-batches processed: 3
Total gang sheets created: 3
```

---

## Strategy 2: Reduce Gang Sheet Max Height ⭐⭐⭐ (QUICK WIN)

**What:** Lower default max_height_inches from 215" to 100"
**Impact:** High - Reduces gang sheet memory by ~50%
**Complexity:** Low - just change printer settings

### Why This Helps

```python
# At 215 inches:
16" × 215" @ 400 DPI = 6,400 × 86,000 pixels = 2.1GB

# At 100 inches (railway optimized):
16" × 100" @ 400 DPI = 6,400 × 40,000 pixels = 0.98GB
# ↑ Less than half the memory!
```

### Implementation

**Option A: Update Printer Settings (per user)**

```sql
UPDATE printers
SET max_height_inches = 100
WHERE user_id = 'your_user_id';
```

**Option B: Force Railway Limit (global)**

In `railway_memory_optimizer.py` (already added):

```python
RAILWAY_MAX_HEIGHT_INCHES = 100  # Force 100" max in Railway
```

Then in orders/service.py:

```python
from server.src.utils.railway_memory_optimizer import RAILWAY_MAX_HEIGHT_INCHES

# Cap height for Railway
if os.getenv('RAILWAY_ENVIRONMENT'):
    gang_sheet_max_height = min(gang_sheet_max_height, RAILWAY_MAX_HEIGHT_INCHES)
    logger.info(f"🚂 Railway: Capping height to {RAILWAY_MAX_HEIGHT_INCHES}\"")
```

**Trade-off:** More gang sheet parts, but no OOM

---

## Strategy 3: Immediate Design Disposal ⭐⭐ (ALREADY IMPLEMENTED)

**What:** Delete designs from memory immediately after all copies placed
**Impact:** Medium - Frees 50-150MB per design
**Complexity:** Low - already implemented

**Status:** ✅ Already active in gangsheet_engine.py

**Verify it's working:**

```
Completed all items for key UV840.png 3x3
🗑️  Freeing design from memory: UV840.png (index 3)
   ✓ Freed 0.12GB (3.45GB → 3.33GB)
```

---

## Strategy 4: Memory-Mapped Gang Sheets ⭐⭐ (ALREADY IMPLEMENTED)

**What:** Use disk-backed arrays for gang sheets >500MB
**Impact:** Medium - Trades memory for I/O
**Complexity:** Low - already implemented

**Status:** ✅ Already active when gang sheets >500MB

**Configuration:**

```python
# In gangsheet_engine.py, line ~703:
GANGSHEET_MEMMAP_THRESHOLD_GB = 0.5  # Use disk for sheets >500MB

# To be more aggressive (use disk for smaller sheets):
GANGSHEET_MEMMAP_THRESHOLD_GB = 0.3  # Use disk for sheets >300MB
```

**Expected Logs:**

```
📦 Allocating gang sheet: 9600x40000 (1.46GB)
💾 Using memory-mapped file (size > 0.5GB)
   Temp file: /tmp/tmp_gangsheet_a3b4c5d6
```

---

## Strategy 5: Tile-Based Processing ⭐⭐ (ADVANCED)

**What:** Process gang sheet in tiles instead of loading entire sheet
**Impact:** High - Can reduce memory by 70%+
**Complexity:** High - requires significant refactoring

### Concept

```python
# Current: Load entire gang sheet into memory
gang_sheet = np.zeros((86000, 6400, 4))  # 2.1GB

# Tile-based: Process in 10x10" tiles
for tile_y in range(0, height, tile_height):
    for tile_x in range(0, width, tile_width):
        tile = process_tile(tile_x, tile_y, 10, 10)  # Only 160MB
        save_tile(tile)
        del tile  # Immediate cleanup
```

**Implementation:** Complex - requires rewriting gangsheet_engine.py

**When to Use:** If all other strategies fail

---

## Strategy 6: Reduce Image Quality Temporarily ⭐ (NUCLEAR OPTION)

**What:** Downsample designs during processing, upsample on save
**Impact:** Medium - Reduces memory during processing
**Complexity:** Medium
**Trade-off:** Slight quality loss if not careful

```python
# Load design at full resolution
design = load_image(path)  # 4000x4000 = 64MB

# Downsample to 75% during processing
design_temp = cv2.resize(design, None, fx=0.75, fy=0.75)  # 3000x3000 = 36MB

# Place on gang sheet
place_design(design_temp)

# Delete immediately
del design, design_temp

# On save, upsample gang sheet back to full resolution
```

**When to Use:** Last resort if other strategies don't work

---

## Strategy 7: Progressive Gang Sheet Saving ⭐ (ADVANCED)

**What:** Save gang sheet incrementally as layers are added
**Impact:** High - Never holds full gang sheet in memory
**Complexity:** Very high

**Concept:**

```python
# Instead of:
gang_sheet = np.zeros((height, width, 4))  # 2.1GB
for design in designs:
    place_design_on_sheet(gang_sheet, design)
save(gang_sheet)

# Progressive saving:
output_file = open_psd_for_writing()
for design in designs:
    layer = create_layer(design)  # 50MB
    write_layer_to_file(output_file, layer)  # Stream to disk
    del layer  # Immediate cleanup
close(output_file)
```

**Implementation:** Very complex - requires PSD/PNG streaming library

---

## Strategy 8: Pre-Flight Memory Check ⭐⭐⭐ (RECOMMENDED)

**What:** Calculate total memory needed before starting, abort if too large
**Impact:** High - Prevents OOM before it happens
**Complexity:** Low - already partially implemented

### Enhanced Implementation

Add to orders/service.py before gang sheet creation:

```python
def estimate_total_memory_needed(order_items_data, gang_sheet_dpi, max_height_inches):
    """Estimate total memory needed for gang sheet creation"""

    # Estimate unique design memory
    unique_designs = len(set(order_items_data.get('Title', [])))
    avg_design_size_mb = 80  # Rough average
    designs_memory_gb = (unique_designs * avg_design_size_mb) / 1024

    # Estimate gang sheet memory (assume fills 70% of height)
    estimated_height = max_height_inches * 0.7
    gang_sheet_memory_gb = (16 * gang_sheet_dpi * estimated_height * gang_sheet_dpi * 4) / (1024**3)

    # Add overhead (image processing, Python objects, etc.)
    overhead_gb = 1.5

    total_estimated_gb = designs_memory_gb + gang_sheet_memory_gb + overhead_gb

    return {
        'designs_gb': designs_memory_gb,
        'gang_sheet_gb': gang_sheet_memory_gb,
        'overhead_gb': overhead_gb,
        'total_gb': total_estimated_gb
    }

# Before creating gang sheets:
estimate = estimate_total_memory_needed(order_items_data, gang_sheet_dpi, gang_sheet_max_height)

logger.info(f"📊 Memory Estimate:")
logger.info(f"   Designs: {estimate['designs_gb']:.2f}GB")
logger.info(f"   Gang sheet: {estimate['gang_sheet_gb']:.2f}GB")
logger.info(f"   Overhead: {estimate['overhead_gb']:.2f}GB")
logger.info(f"   Total: {estimate['total_gb']:.2f}GB")

if estimate['total_gb'] > 6.0:  # Leave 2GB headroom
    logger.error(f"❌ Estimated memory {estimate['total_gb']:.2f}GB exceeds safe limit (6GB)")
    logger.error(f"💡 Solutions:")
    logger.error(f"   1. Process fewer orders (currently {len(order_items_data.get('Title', []))} items)")
    logger.error(f"   2. Reduce max_height_inches (currently {gang_sheet_max_height}\")")
    logger.error(f"   3. Use auto-split batching (recommended)")
    return {
        'success': False,
        'error': f'Batch too large: estimated {estimate["total_gb"]:.2f}GB (limit 6GB)',
        'recommendation': 'Reduce batch size or enable auto-splitting'
    }
```

---

## Strategy 9: Environment-Based Limits ⭐⭐ (QUICK WIN)

**What:** Apply different limits in Railway vs local development
**Impact:** Medium - Prevents Railway-specific OOM
**Complexity:** Low

### Implementation

```python
import os

# Detect Railway environment
IN_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None

if IN_RAILWAY:
    # Railway-specific limits (8GB container)
    MAX_HEIGHT_INCHES = 100
    MAX_ITEMS_PER_BATCH = 15
    MAX_GANG_SHEET_MEMORY_GB = 2.0
    MEMORY_PAUSE_THRESHOLD = 0.75  # Pause earlier
    CHECK_FREQUENCY = 5  # Check every 5 items
    logger.info("🚂 Railway environment detected - using conservative limits")
else:
    # Local development limits (more permissive)
    MAX_HEIGHT_INCHES = 215
    MAX_ITEMS_PER_BATCH = 50
    MAX_GANG_SHEET_MEMORY_GB = 3.0
    MEMORY_PAUSE_THRESHOLD = 0.87
    CHECK_FREQUENCY = 10
    logger.info("💻 Local environment - using standard limits")
```

---

## Strategy 10: Upgrade Railway Plan ⭐⭐⭐ (EASIEST)

**What:** Upgrade from Hobby (8GB) to Pro (32GB)
**Impact:** Very high - 4x more memory
**Complexity:** None - just costs money

**Railway Plans:**

- Hobby: 8GB RAM ($5/month)
- Pro: 32GB RAM ($20/month)
- Enterprise: Custom (contact sales)

**When to Upgrade:**

- If gang sheets must be large (>100" height)
- If processing many orders per batch is critical
- If dev time costs more than $15/month difference

---

## Recommended Implementation Order

### Immediate (Do These First):

1. **✅ Already Applied:** Force 8GB detection
2. **✅ Already Applied:** Lower pause threshold to 80%
3. **✅ Already Applied:** Check memory every 5 items
4. **⭐ NEW:** Reduce max_height_inches to 100"
5. **⭐ NEW:** Add pre-flight memory check

### Short Term (Next Few Days):

6. **⭐ NEW:** Integrate auto-batch splitting
7. **⭐ NEW:** Environment-based limits

### If Still Having Issues:

8. Lower GANGSHEET_MEMMAP_THRESHOLD_GB to 0.3
9. Reduce max_items_per_batch to 10
10. Lower MEMORY_PAUSE_THRESHOLD to 0.70

### If Everything Else Fails:

11. Implement tile-based processing (complex)
12. Upgrade Railway plan to 32GB

---

## Quick Wins You Can Apply Right Now

### 1. Cap Height to 100" (1 line change)

In `orders/service.py` around line 750:

```python
# After fetching gang_sheet_max_height:
if os.getenv('RAILWAY_ENVIRONMENT'):
    gang_sheet_max_height = min(gang_sheet_max_height, 100)
    logging.info(f"🚂 Railway: Capping height to 100\"")
```

### 2. Lower Max Gang Sheet Memory (1 line change)

In `railway_memory_optimizer.py` line ~24:

```python
MAX_GANG_SHEET_MEMORY_GB = 2.0  # Was 3.0
```

### 3. Add Pre-Flight Check (10 lines)

In `orders/service.py` before `create_gang_sheets`:

```python
# Quick estimate
unique_designs = len(set(order_items_data['Title']))
estimated_gb = (unique_designs * 0.08) + 2.5  # 80MB per design + 2.5GB gang sheet

if estimated_gb > 6.0:
    logging.error(f"❌ Estimated {estimated_gb:.1f}GB > 6GB limit")
    return {
        'success': False,
        'error': f'Batch too large ({len(order_items_data["Title"])} items)',
        'recommendation': 'Process 10-15 orders at a time'
    }
```

---

## Summary: What to Do Next

**Highest Impact, Lowest Effort:**

1. ✅ Cap max_height to 100" (1 line)
2. ✅ Lower MAX_GANG_SHEET_MEMORY_GB to 2.0 (already done)
3. ✅ Add pre-flight memory check (10 lines)

**High Impact, Medium Effort:** 4. Integrate auto-batch splitting (modify orders/service.py)

**If Still Issues:** 5. Lower pause threshold to 0.70 (from 0.80) 6. Check memory every 3 items (from 5) 7. Process max 10 orders per batch (from 15)

**Nuclear Option:** 8. Upgrade Railway to 32GB plan

**Test After Each Change:**

- Create gang sheet with 15-20 orders
- Monitor logs for pause/resume
- Verify no OOM
- If successful, gradually increase batch size
