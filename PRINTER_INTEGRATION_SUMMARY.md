# Printer Integration & Canvas Config Enhancement

This document summarizes the implementation of printer management and canvas configuration enhancements to eliminate hard-coded dependencies in the gangsheet engine.

## 🖨️ New Printer Entity

### Features

- **User-specific printers**: Each user can have multiple printers with different capabilities
- **Template compatibility**: Printers can be configured to support specific templates
- **Print area constraints**: Max width/height in inches for print area validation
- **DPI configuration**: Configurable DPI settings with suggestions (300, 400, 500, 600)
- **Default printer**: Users can set one printer as their default
- **Printer types**: Support for various printer types (inkjet, laser, sublimation, DTG, vinyl, UV, other)

### Database Schema (`printers` table)

```sql
CREATE TABLE printers (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    printer_type VARCHAR(50) NOT NULL DEFAULT 'inkjet',
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    description TEXT,
    max_width_inches FLOAT NOT NULL,
    max_height_inches FLOAT NOT NULL,
    dpi INTEGER NOT NULL DEFAULT 300,
    supported_template_ids UUID[] DEFAULT ARRAY[]::uuid[],
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Relationships

- **Many-to-One with User**: `users.printers` (cascade delete)
- **Many-to-One with Organization**: Organization-scoped printers
- **Template Support**: Array of supported template UUIDs

## 📐 Enhanced Canvas Config

### New Fields Added to `canvas_configs` table

```sql
-- Print quality configuration
dpi INTEGER NOT NULL DEFAULT 300

-- Gang sheet spacing configuration (in inches)
spacing_width_inches FLOAT NOT NULL DEFAULT 0.125  -- 1/8 inch default
spacing_height_inches FLOAT NOT NULL DEFAULT 0.125 -- 1/8 inch default
```

### Canvas Config Benefits

- **DPI per canvas**: Each canvas config has its own DPI for design storage/processing
- **Spacing control**: Configurable spacing between designs in gang sheets
- **Template-specific settings**: Different templates can have different quality/spacing requirements

## 🔌 API Endpoints

### Printer Management (`/api/printers`)

#### Create Printer

```
POST /api/printers/
```

- Create new printer with type, dimensions, DPI, template support
- Automatically handles default printer logic

#### List User Printers

```
GET /api/printers/?active_only=true&skip=0&limit=100
```

- Get paginated list of user's printers
- Filter by active status
- Ordered by default first, then by name

#### Printer Details

```
GET /api/printers/{printer_id}
```

- Get specific printer details
- Ownership verification

#### Update Printer

```
PUT /api/printers/{printer_id}
```

- Update printer configuration
- Handles default printer changes

#### Delete Printer

```
DELETE /api/printers/{printer_id}
```

- Soft delete with audit logging

#### Capability Checking

```
POST /api/printers/{printer_id}/check-capability
{
    "width_inches": 8.5,
    "height_inches": 11.0,
    "template_id": "uuid-optional"
}
```

- Check if printer can handle specific dimensions
- Validate template compatibility
- Returns detailed capability analysis

#### Find Compatible Printers

```
GET /api/printers/compatible/find?width_inches=8.5&height_inches=11&template_id=uuid
```

- Find all user printers that can handle given requirements
- Ordered by default first, then by DPI

#### Default Printer Management

```
GET /api/printers/default/get
POST /api/printers/{printer_id}/set-default
```

- Get/set user's default printer
- Automatically unsets previous default

#### Statistics

```
GET /api/printers/stats/summary
```

- Total/active printer counts
- Breakdown by printer type
- Average DPI
- Default printer identification

#### Configuration Suggestions

```
GET /api/printers/suggestions/config
```

- Suggested DPI values: [300, 400, 500, 600]
- Available printer types
- Common paper sizes with descriptions

## 🏗️ Integration with Gangsheet Engine

### Eliminating Hard-coded Dependencies

#### Before (Hard-coded)

```python
# Hard-coded values in gangsheet engine
DPI = 300
SPACING_WIDTH = 0.125
SPACING_HEIGHT = 0.125
MAX_PRINT_WIDTH = 8.5
MAX_PRINT_HEIGHT = 11.0
```

#### After (Dynamic Configuration)

```python
# Get user's default printer and canvas config
default_printer = PrinterService.get_default_printer(db, user_id, org_id)
canvas_config = get_canvas_config_for_template(template_id)

# Use printer constraints for validation
if not default_printer.can_print_size(width_inches, height_inches):
    # Find compatible printer or show error
    compatible_printers = PrinterService.find_compatible_printers(...)

# Use canvas config for spacing and DPI
spacing_width = canvas_config.spacing_width_inches
spacing_height = canvas_config.spacing_height_inches
dpi = canvas_config.dpi

# Convert to pixels using canvas DPI
spacing_width_pixels, spacing_height_pixels = canvas_config.get_spacing_pixels()
```

### Gangsheet Engine Workflow

1. **Get Requirements**: Determine canvas config and print dimensions
2. **Find Printer**: Get default printer or find compatible one
3. **Validate Capability**: Ensure printer can handle the job
4. **Apply Settings**: Use printer DPI and canvas spacing
5. **Generate Gang Sheet**: Create optimized layout with proper spacing

### Usage in Gangsheet Generation

```python
from server.src.routes.printers.service import PrinterService
from server.src.entities.canvas_config import CanvasConfig

def generate_gangsheet(user_id: UUID, org_id: UUID, template_id: UUID, designs: List[Design]):
    # Get user's default printer
    printer = PrinterService.get_default_printer(db, user_id, org_id)
    if not printer:
        raise ValueError("No default printer configured")

    # Get canvas configuration
    canvas_config = get_canvas_config_for_template(template_id)

    # Validate printer can handle the template
    if not printer.supports_template(template_id):
        compatible_printers = PrinterService.find_compatible_printers(
            db, user_id, org_id,
            canvas_config.width_inches,
            canvas_config.height_inches,
            template_id
        )
        if not compatible_printers:
            raise ValueError("No compatible printer found")
        printer = compatible_printers[0]  # Use best match

    # Generate gang sheet with printer constraints and canvas settings
    return create_gang_sheet(
        designs=designs,
        max_width_inches=printer.max_width_inches,
        max_height_inches=printer.max_height_inches,
        printer_dpi=printer.dpi,
        spacing_width=canvas_config.spacing_width_inches,
        spacing_height=canvas_config.spacing_height_inches,
        canvas_dpi=canvas_config.dpi
    )
```

## 🗄️ Database Migration

### Migration File

`migration_add_printers_and_canvas_updates.py`

### Running the Migration

```bash
# Direct execution
python migration_add_printers_and_canvas_updates.py

# Or via Alembic (if configured)
alembic upgrade head
```

### Migration Actions

1. **Create printers table** with proper relationships and constraints
2. **Add indexes** for performance optimization
3. **Update canvas_configs** with DPI and spacing fields
4. **Add unique constraint** to ensure only one default printer per user
5. **Handle existing data** with sensible defaults

## 📊 Benefits

### For Gangsheet Engine

- **No more hard-coded values**: All settings come from user configuration
- **Printer-aware generation**: Respects actual printer constraints
- **Template-specific spacing**: Different products can have different spacing needs
- **Quality control**: DPI settings per canvas type for optimal output

### For Users

- **Multiple printer support**: Configure different printers for different jobs
- **Realistic constraints**: System prevents impossible print jobs
- **Template compatibility**: Know which printers work with which templates
- **Default workflow**: Set preferred printer for streamlined workflow

### for Developers

- **Maintainable code**: Configuration-driven instead of hard-coded
- **Extensible**: Easy to add new printer types and capabilities
- **Testable**: Mock different printer configurations for testing
- **Auditable**: All printer changes logged for troubleshooting

## 🔧 Usage Examples

### Setting Up a New Printer

```javascript
// Create new printer via API
const printer = await fetch("/api/printers/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    name: "Epson EcoTank L3250",
    printer_type: "inkjet",
    manufacturer: "Epson",
    model: "EcoTank L3250",
    max_width_inches: 8.5,
    max_height_inches: 11.7,
    dpi: 300,
    supported_template_ids: [template1_uuid, template2_uuid],
    is_default: true,
  }),
});
```

### Updating Canvas Config for Better Quality

```python
# Update canvas config with higher DPI and tighter spacing
canvas_config.dpi = 600  # Higher quality for detailed designs
canvas_config.spacing_width_inches = 0.0625  # 1/16 inch spacing
canvas_config.spacing_height_inches = 0.0625
```

### Checking Print Compatibility

```javascript
// Check if printer can handle a specific job
const capability = await fetch(`/api/printers/${printerId}/check-capability`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    width_inches: 8.5,
    height_inches: 11.0,
    template_id: "uuid-of-template",
  }),
});

if (!capability.can_print) {
  console.log(`Cannot print: ${capability.reason}`);
}
```

## 🚀 Next Steps

### Integration Tasks

1. **Update gangsheet engine** to use printer and canvas configurations
2. **Add printer selection UI** in frontend for job creation
3. **Implement printer recommendations** based on job requirements
4. **Add print preview** showing actual printer constraints
5. **Create printer setup wizard** for new users

### Future Enhancements

- **Printer profiles** with color management settings
- **Cost estimation** based on printer specifications
- **Print queue management** for multiple printers
- **Automatic printer selection** based on job requirements
- **Print history tracking** per printer
- **Maintenance scheduling** and reminders

This implementation provides a solid foundation for eliminating hard-coded dependencies while giving users full control over their printing workflow.
