# Use Database Dimensions and DPI for Gang Sheets

## Issue

User reported: "The dimension in terms of inches and DPI should be coming from the printers table"

## Problem

Gang sheet creation was using **hardcoded values** instead of database configuration:

```python
result = create_gang_sheets(
    image_data=order_items_data,
    image_type=template_name,
    output_path=output_dir,
    total_images=len(order_items_data.get('Title', [])),
    dpi=400,  # ❌ HARDCODED
    std_dpi=400,  # ❌ HARDCODED
    # No max_width_inches or max_height_inches passed
    # Falls back to constants GANG_SHEET_MAX_WIDTH, GANG_SHEET_MAX_HEIGHT
    file_format=format
)
```

**Issues:**

1. DPI hardcoded to 400 - ignores printer settings
2. Width/height fall back to constants (23" × 215") - ignores DB config
3. User configuration in printers table ignored
4. Inconsistent output across different printers

## Database Schema

### Printer Table

```python
class Printer:
    id: int
    user_id: str
    name: str
    dpi: int                    # ✅ Used for gang sheet DPI
    max_width_inches: float     # ✅ Used for gang sheet max width
    is_default: bool
    is_active: bool
```

### CanvasConfig Table

```python
class CanvasConfig:
    id: int
    template_id: int
    name: str
    max_height_inches: float    # ✅ Used for gang sheet max height
    is_active: bool
```

### Relationship

- Printer: Defines machine capabilities (DPI, max width)
- CanvasConfig: Defines template-specific max height
- Together: Define gang sheet dimensions

## Solution

### 1. Fetch Full Printer Object (Not Just ID)

**Before:**

```python
if printer_id is None:
    default_printer = db.query(Printer).filter(...).first()
    if default_printer:
        printer_id = default_printer.id  # ❌ Only stored ID
        logging.info(f"Using default printer: {default_printer.name}")
# printer object lost, only have ID
```

**After:**

```python
printer = None
if printer_id is None:
    printer = db.query(Printer).filter(...).first()  # ✅ Keep object
    if printer:
        printer_id = printer.id
        logging.info(f"Using default printer: {printer.name}")
else:
    # Fetch printer by ID if provided
    printer = db.query(Printer).filter(
        Printer.id == printer_id,
        Printer.user_id == user_id
    ).first()

if not printer:
    return {"success": False, "error": "No printer found"}
```

### 2. Fetch Full CanvasConfig Object

**Before:**

```python
if canvas_config_id is None and template and template.canvas_configs:
    for canvas in template.canvas_configs:
        if canvas.is_active:
            canvas_config_id = canvas.id  # ❌ Only stored ID
            logging.info(f"Using canvas config: {canvas.name}")
            break
# canvas_config object lost, only have ID
```

**After:**

```python
canvas_config = None
if canvas_config_id is None and template and template.canvas_configs:
    for canvas in template.canvas_configs:
        if canvas.is_active:
            canvas_config = canvas  # ✅ Keep object
            canvas_config_id = canvas.id
            logging.info(f"Using canvas config: {canvas.name}")
            break
else:
    # Fetch canvas config by ID if provided
    canvas_config = db.query(CanvasConfig).filter(
        CanvasConfig.id == canvas_config_id
    ).first()

if not canvas_config:
    return {"success": False, "error": "No canvas configuration found"}
```

### 3. Extract Dimensions and DPI from Database

**Added:**

```python
# Extract dimensions and DPI from database
gang_sheet_dpi = printer.dpi if printer.dpi else 400
gang_sheet_max_width = printer.max_width_inches if printer.max_width_inches else 23
gang_sheet_max_height = canvas_config.max_height_inches if canvas_config.max_height_inches else 215

logging.info(f"📐 Gang sheet config from DB: {gang_sheet_max_width}\"W × {gang_sheet_max_height}\"H @ {gang_sheet_dpi} DPI")
logging.info(f"   Printer: {printer.name} (ID: {printer.id})")
logging.info(f"   Canvas: {canvas_config.name} (ID: {canvas_config.id})")
```

**Fallback values:**

- If `printer.dpi` is None: default to 400
- If `printer.max_width_inches` is None: default to 23
- If `canvas_config.max_height_inches` is None: default to 215

### 4. Pass to Gang Sheet Creation

**Before:**

```python
result = create_gang_sheets(
    image_data=order_items_data,
    image_type=template_name,
    output_path=output_dir,
    total_images=len(order_items_data.get('Title', [])),
    dpi=400,  # ❌ HARDCODED
    std_dpi=400,  # ❌ HARDCODED
    file_format=format
)
```

**After:**

```python
result = create_gang_sheets(
    image_data=order_items_data,
    image_type=template_name,
    output_path=output_dir,
    total_images=len(order_items_data.get('Title', [])),
    max_width_inches=gang_sheet_max_width,  # ✅ From printer.max_width_inches
    max_height_inches=gang_sheet_max_height,  # ✅ From canvas_config.max_height_inches
    dpi=gang_sheet_dpi,  # ✅ From printer.dpi
    std_dpi=gang_sheet_dpi,  # ✅ From printer.dpi
    file_format=format
)
```

## Files Modified

### server/src/routes/orders/service.py

**Function 1: `create_print_files` (lines 219-272)**

- Fetch full printer object (not just ID)
- Fetch full canvas_config object (not just ID)
- Extract dimensions and DPI from database
- Pass to create_gang_sheets (line 405)

**Function 2: `create_print_files_from_selected_orders` (lines 641-721, 842)**

- Same changes as above
- Pass to create_gang_sheets (line 842)

## Expected Log Output

### Database Configuration Loaded:

```
Using default printer: Epson SureColor F570
📐 Gang sheet config from DB: 24.0"W × 100.0"H @ 720 DPI
   Printer: Epson SureColor F570 (ID: 123)
   Canvas: UVDTF 16oz Standard (ID: 456)
Database configuration fetch completed in 0.045s
```

### Gang Sheet Creation:

```
Gang sheet dimensions: 24.0"×100.0" = 9600×40000 pixels at 720 DPI
```

Shows actual database values being used!

## Validation

### Error Handling:

**No printer configured:**

```json
{
  "success": false,
  "error": "No printer found. Please configure a printer in settings."
}
```

**No canvas config for template:**

```json
{
  "success": false,
  "error": "No canvas configuration found for template 'UVDTF 16oz'"
}
```

## Example Configurations

### Example 1: DTF Printer

```python
# Database:
Printer:
  name: "Epson F2100"
  dpi: 720
  max_width_inches: 16.0

CanvasConfig:
  name: "DTF Standard"
  max_height_inches: 22.0

# Result:
Gang sheet: 16.0" × 22.0" @ 720 DPI
```

### Example 2: UV Printer

```python
# Database:
Printer:
  name: "Roland VersaUV LEF2-300"
  dpi: 1440
  max_width_inches: 30.0

CanvasConfig:
  name: "UV Large Format"
  max_height_inches: 20.0

# Result:
Gang sheet: 30.0" × 20.0" @ 1440 DPI
```

### Example 3: UVDTF Printer

```python
# Database:
Printer:
  name: "UVDTF 16oz Printer"
  dpi: 400
  max_width_inches: 23.0

CanvasConfig:
  name: "UVDTF 16oz"
  max_height_inches: 215.0

# Result:
Gang sheet: 23.0" × 215.0" @ 400 DPI
```

## Benefits

### 1. User Configuration Respected

- Each user can configure their own printer specs
- Different printers = different dimensions
- No more one-size-fits-all approach

### 2. Template-Specific Heights

- Different templates can have different max heights
- UVDTF 16oz: 215 inches (continuous roll)
- DTF: 22 inches (sheet size)
- Flexible per template

### 3. DPI Accuracy

- High-end printer: 1440 DPI
- Standard printer: 720 DPI
- Budget printer: 400 DPI
- Output matches printer capability

### 4. Consistency

- All gang sheets use same source of truth (database)
- No hardcoded values to maintain
- Change printer settings → immediate effect

### 5. Multi-Printer Support

- User can have multiple printers
- Each with different specs
- Select printer → get correct dimensions

## Migration Notes

### Existing Users:

If printer or canvas_config has NULL values:

- `dpi = NULL` → falls back to 400
- `max_width_inches = NULL` → falls back to 23
- `max_height_inches = NULL` → falls back to 215

**Action:** Update database with actual printer specs!

### New Users:

Must configure:

1. Printer with DPI and max_width_inches
2. Canvas config with max_height_inches
3. Set one printer as default

## Testing

### Test 1: Verify Database Values Used

```python
# Set in database:
printer.dpi = 720
printer.max_width_inches = 16.0
canvas_config.max_height_inches = 22.0

# Check logs:
"📐 Gang sheet config from DB: 16.0\"W × 22.0\"H @ 720 DPI"
"Gang sheet dimensions: 16.0\"×22.0\" = 4608×6336 pixels at 720 DPI"
```

### Test 2: Fallback Values

```python
# Set in database:
printer.dpi = None
printer.max_width_inches = None
canvas_config.max_height_inches = None

# Check logs:
"📐 Gang sheet config from DB: 23.0\"W × 215.0\"H @ 400 DPI"
```

### Test 3: Multiple Printers

```python
# User has 2 printers:
# 1. DTF Printer (720 DPI, 16"W)
# 2. UV Printer (1440 DPI, 30"W)

# Select DTF printer → Get 16" width @ 720 DPI
# Select UV printer → Get 30" width @ 1440 DPI
```

## Summary

**Problem:** Gang sheets used hardcoded DPI (400) and dimensions (23" × 215")

**Solution:** Fetch printer and canvas_config objects from database, extract dimensions and DPI

**Changes:**

1. Fetch full Printer object (not just ID)
2. Fetch full CanvasConfig object (not just ID)
3. Extract gang_sheet_dpi, gang_sheet_max_width, gang_sheet_max_height
4. Pass to create_gang_sheets function

**Result:**

- Gang sheets respect user's printer configuration
- Different printers → different dimensions/DPI
- Template-specific heights via canvas_config
- Database is single source of truth

**All gang sheet dimensions and DPI now come from the database! ✅**
