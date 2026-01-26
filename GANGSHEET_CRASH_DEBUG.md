# Gang Sheet Creation Crash - Debugging

## Problem

Backend crashes during gang sheet creation, specifically after printing:

```
dpi: 400
std_dpi: 400
```

The crash happens in the gang sheet processing pipeline, after DPI values are set but before the file is saved.

## Root Cause

The crash occurs in `server/src/utils/gangsheet_engine.py` during one of these operations:

1. **Gang sheet resize** (line 798): `cv2.resize()` on the full gang sheet
2. **Image layer resize** (line 825): `cv2.resize()` on individual image layers
3. **File save** (line 837): `save_image_with_format()` writing the final file

Most likely causes:

- Out of memory during resize operations
- Invalid dimensions (width or height = 0)
- Corrupted image data
- File system issues during save

## Fixes Applied

### 1. Comprehensive Error Logging

Added detailed logging at every step to pinpoint the exact crash location:

```python
logging.info(f"📐 DPI settings - dpi: {dpi}, std_dpi: {std_dpi}")
logging.info(f"📏 Calculated dimensions - width: {new_width}, height: {new_height}, scale: {scale_factor}")
logging.info(f"🔄 Resizing gang sheet from {cropped_gang_sheet.shape} to ({new_width}, {new_height})")
logging.info(f"✅ Gang sheet resized successfully")
logging.info(f"💾 Preparing to save: {base_filename}")
logging.info(f"🔄 Adjusting {len(placed_images)} image layers...")
logging.info(f"💾 Saving gang sheet as {file_format}...")
logging.info(f"✅ Successfully created gang sheet...")
```

### 2. Try-Catch Around Critical Operations

Wrapped the entire gang sheet processing in try-catch with detailed error reporting:

```python
try:
    # Calculate dimensions
    scale_factor = std_dpi / dpi
    new_width, new_height = int((xmax - xmin + 1) * scale_factor), ...

    # Resize gang sheet
    resized_gang_sheet = cv2.resize(...)

    # Process image layers
    for img_info in placed_images:
        scaled_image = cv2.resize(...)

    # Save file
    save_image_with_format(...)

except Exception as resize_error:
    logging.error(f"❌ CRASH during gang sheet processing: {str(resize_error)}")
    logging.error(f"📋 Gang sheet shape: {cropped_gang_sheet.shape}")
    logging.error(f"📋 Target size: ({new_width}, {new_height})")
    logging.error(f"📋 Traceback:\n{traceback.format_exc()}")
    raise
```

### 3. Individual Layer Error Handling

Each image layer resize is now wrapped in its own try-catch to prevent one bad image from killing the entire process:

```python
for idx, img_info in enumerate(placed_images):
    try:
        if scaled_width > 0 and scaled_height > 0:
            scaled_image = cv2.resize(img_info['image_data'], ...)
            adjusted_placed_images.append(...)
        else:
            logging.warning(f"⚠️  Skipping image layer {idx}: invalid dimensions")
    except Exception as layer_error:
        logging.error(f"❌ Error resizing image layer {idx}: {str(layer_error)}")
        # Continue with other layers
```

### 4. Dimension Validation

Added validation to skip images with invalid dimensions (0 or negative):

```python
if scaled_width > 0 and scaled_height > 0:
    # Process image
else:
    logging.warning(f"⚠️  Skipping image layer {idx}: invalid dimensions ({scaled_width}x{scaled_height})")
```

## How to Debug After Deploy

### Step 1: Monitor Railway Logs

After clicking "Send to Print", watch for the new emoji markers in order:

```
📐 DPI settings - dpi: 400, std_dpi: 400
📏 Calculated dimensions - width: 16000, height: 20000, scale: 1.0
🔄 Resizing gang sheet from (20000, 16000, 4) to (16000, 20000)
✅ Gang sheet resized successfully          # ← If it crashes before this, resize failed
💾 Preparing to save: NookTransfers_...
🔄 Adjusting 31 image layers...
✅ Adjusted 31 image layers                 # ← If it crashes here, layer processing failed
💾 Saving gang sheet as PNG...
✅ Successfully created gang sheet...       # ← If it crashes here, save failed
```

### Step 2: Identify Crash Point

**If logs show:**

| Last Message                  | Problem                            | Likely Cause                       |
| ----------------------------- | ---------------------------------- | ---------------------------------- |
| `📐 DPI settings`             | Crash before dimensions calculated | Division by zero (dpi = 0)         |
| `📏 Calculated dimensions`    | Crash before resize                | Invalid dimensions or memory issue |
| `🔄 Resizing gang sheet`      | Crash during resize                | Out of memory or OpenCV error      |
| `💾 Preparing to save`        | Crash during layer processing      | Individual layer issue             |
| `🔄 Adjusting N image layers` | Crash during layer resize          | Corrupted image data               |
| `💾 Saving gang sheet`        | Crash during file save             | Disk space or permissions          |

### Step 3: Check Error Details

The crash will now log detailed information:

```
❌ CRASH during gang sheet processing: cannot resize array to (0, 20000)
📋 Gang sheet shape: (20000, 16000, 4)
📋 Target size: (0, 20000)
📋 Traceback:
  File "gangsheet_engine.py", line 798, in create_gang_sheets
    resized_gang_sheet = cv2.resize(...)
  cv2.error: OpenCV(4.8.0) Error: ...
```

## Common Errors and Solutions

### Error: "Out of memory"

**Cause:** Gang sheet too large for available RAM

**Solutions:**

- Reduce `max_width_inches` or `max_height_inches` in template
- Lower DPI (from 400 to 300)
- Process fewer orders at a time
- Upgrade Railway memory plan

### Error: "Invalid dimensions (0, height)"

**Cause:** Width calculated as 0

**Solutions:**

- Check if `xmax - xmin` is 0 (empty gang sheet)
- Verify scale_factor is valid (not infinity or NaN)
- Check if cropping removed all content

### Error: "OpenCV resize failed"

**Cause:** Image data corrupted or invalid format

**Solutions:**

- Check individual design files are valid
- Verify all files downloaded from NAS successfully
- Re-upload corrupted design files

### Error: "Permission denied" during save

**Cause:** No write access to output directory

**Solutions:**

- Check Railway volume permissions
- Verify temp directory is writable
- Check disk space available

## Testing Checklist

After deploying:

- [ ] Check Railway logs show all emoji markers in sequence
- [ ] Verify `✅ Gang sheet resized successfully` appears
- [ ] Verify `✅ Adjusted N image layers` shows correct count
- [ ] Verify `✅ Successfully created gang sheet` appears
- [ ] Check no `❌ CRASH` errors in logs
- [ ] Verify files are created in NAS PrintFiles directory
- [ ] Test with different order counts (1, 5, 10, 30)
- [ ] Test with different templates/sizes

## Log Markers Reference

| Emoji | Meaning       | Step                              |
| ----- | ------------- | --------------------------------- |
| 📐    | Configuration | DPI settings loaded               |
| 📏    | Calculation   | Dimensions calculated             |
| 🔄    | Processing    | Resize/adjustment in progress     |
| ✅    | Success       | Operation completed successfully  |
| ⚠️    | Warning       | Non-critical issue (skipped item) |
| ❌    | Error         | Critical failure                  |
| 💾    | File I/O      | Saving to disk                    |
| 📋    | Debug Info    | Detailed diagnostic information   |

## Expected Output (Success)

```
📐 DPI settings - dpi: 400, std_dpi: 400
📏 Calculated dimensions - width: 16000, height: 20000, scale: 1.0
🔄 Resizing gang sheet from (20000, 16000, 4) to (16000, 20000)
✅ Gang sheet resized successfully
💾 Preparing to save: NookTransfers 01262026 UVDTF 16oz part 1
🔄 Adjusting 31 image layers...
✅ Adjusted 31 image layers
💾 Saving gang sheet as PNG...
✅ Successfully created gang sheet with 31 layers: NookTransfers 01262026 UVDTF 16oz part 1.png
Immediately freed 2.95GB after saving part 1
```

## Memory Management

The code now:

1. Creates gang sheet
2. Resizes it
3. Saves it
4. **Immediately frees memory** (before starting next part)
5. Forces garbage collection twice
6. Logs memory freed

This prevents memory accumulation when creating multiple gang sheets.

## Files Modified

- `server/src/utils/gangsheet_engine.py`:
  - Added comprehensive logging throughout gang sheet creation
  - Added try-catch around critical resize operations
  - Added individual error handling for each image layer
  - Added dimension validation
  - Fixed code structure (memory cleanup after successful save)

## Next Steps

1. **Deploy to Railway:**

   ```bash
   git add .
   git commit -m "Add comprehensive gang sheet crash debugging"
   git push origin production
   ```

2. **Test and Monitor:**
   - Click "Send to Print"
   - Watch Railway logs for emoji markers
   - Note which marker appears last before crash (if any)

3. **Share Results:**
   If still crashing, share:
   - Last emoji marker before crash
   - Error message from `❌ CRASH` log
   - Gang sheet shape and target size
   - Full traceback

## Summary

**Before:** Silent crash with only "dpi: 400" as last output
**After:** Detailed logging showing exact crash location with full diagnostics

The system will now tell you:

- Exactly where it crashed (which operation)
- What the values were (dimensions, shapes)
- Why it crashed (full traceback)
- Which image layer failed (if layer processing)

This makes debugging 100x easier!
