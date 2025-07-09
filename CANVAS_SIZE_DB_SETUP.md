# Canvas and Size Database Configuration

This document describes the database tables and API interface for canvas and size configurations that can be passed into `resizing.py`.

## Overview

The system now supports dynamic canvas and size configurations stored in the database, allowing users to customize their resizing parameters without modifying code.

## Database Tables

### CanvasConfig Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `template_name`: Template name (e.g., 'UVDTF Decal')
- `width_inches`: Canvas width in inches
- `height_inches`: Canvas height in inches
- `description`: Optional description
- `is_active`: Boolean flag for soft deletes
- `created_at`: Timestamp
- `updated_at`: Timestamp

### SizeConfig Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `template_name`: Template name (e.g., 'UVDTF 16oz')
- `size_name`: Size name (e.g., 'Adult+', 'Adult', 'Youth') - nullable
- `width_inches`: Size width in inches
- `height_inches`: Size height in inches
- `description`: Optional description
- `is_active`: Boolean flag for soft deletes
- `created_at`: Timestamp
- `updated_at`: Timestamp

## API Endpoints

### Canvas Configuration Endpoints

- `GET /api/canvas-configs` - List all canvas configurations for current user
- `GET /api/canvas-configs/{config_id}` - Get specific canvas configuration
- `POST /api/canvas-configs` - Create new canvas configuration
- `PUT /api/canvas-configs/{config_id}` - Update canvas configuration
- `DELETE /api/canvas-configs/{config_id}` - Delete canvas configuration (soft delete)

### Size Configuration Endpoints

- `GET /api/size-configs` - List all size configurations for current user
- `GET /api/size-configs/{config_id}` - Get specific size configuration
- `POST /api/size-configs` - Create new size configuration
- `PUT /api/size-configs/{config_id}` - Update size configuration
- `DELETE /api/size-configs/{config_id}` - Delete size configuration (soft delete)

### Resizing Configuration Endpoint

- `GET /api/resizing-configs/{template_name}` - Get canvas and size configurations for a specific template, formatted for resizing.py

## Database Migration

To create the new tables and add default configurations:

```bash
python run_canvas_size_migration.py
```

## Integration with resizing.py

### Option 1: Use the provided utility functions

```python
from server.engine.resizing_db_utils import get_user_resizing_configs

# Get all configurations for a shop
configs = get_user_resizing_configs("shop_name")
if configs:
    canvas_configs = configs['CANVAS']
    size_configs = configs['SIZING']
```

### Option 2: Use the API endpoint

```python
import requests

# Get configurations for a specific template
response = requests.get(f"/api/resizing-configs/UVDTF 16oz")
configs = response.json()
canvas_data = configs['canvas']
sizing_data = configs['sizing']
```

### Option 3: Modify resizing.py directly

See `server/engine/resizing_with_db.py` for an example of how to modify the original resizing.py to use database configurations.

## Example Usage

### Creating a Canvas Configuration

```python
canvas_config = {
    "template_name": "UVDTF Decal",
    "width_inches": 4.0,
    "height_inches": 4.0,
    "description": "4x4 inch decal canvas"
}

response = requests.post("/api/canvas-configs", json=canvas_config)
```

### Creating a Size Configuration

```python
size_config = {
    "template_name": "DTF",
    "size_name": "Adult+",
    "width_inches": 12.0,
    "height_inches": 16.0,
    "description": "Adult+ DTF transfer size"
}

response = requests.post("/api/size-configs", json=size_config)
```

## Data Format for resizing.py

The API returns data in the format expected by resizing.py:

```json
{
  "canvas": {
    "UVDTF Decal": {
      "width": 4.0,
      "height": 4.0
    }
  },
  "sizing": {
    "UVDTF 16oz": {
      "width": 9.5,
      "height": 4.33
    },
    "DTF": {
      "Adult+": {
        "width": 12.0,
        "height": 16.0
      },
      "Adult": {
        "width": 10.0,
        "height": 14.0
      }
    }
  }
}
```

## Default Configurations

The migration script adds these default configurations:

### Canvas Configurations
- UVDTF Decal: 4.0" x 4.0"

### Size Configurations
- UVDTF 16oz: 9.5" x 4.33"
- DTF Adult+: 12.0" x 16.0"
- DTF Adult: 10.0" x 14.0"
- DTF Youth: 8.0" x 12.0"

## Benefits

1. **Dynamic Configuration**: Users can customize canvas and size configurations without code changes
2. **User-Specific Settings**: Each user can have their own configurations
3. **Template Support**: Configurations are organized by template name
4. **Size Variants**: Support for different sizes within the same template (e.g., DTF with Adult+, Adult, Youth)
5. **Backward Compatibility**: Falls back to hardcoded defaults if no database configuration is found
6. **Soft Deletes**: Configurations can be deactivated without losing data

## Files Created/Modified

### New Files
- `server/api/models.py` - Added CanvasConfig and SizeConfig models
- `server/api/routes.py` - Added API endpoints for canvas and size configurations
- `server/engine/resizing_db_utils.py` - Database utility functions for resizing.py
- `server/migrations/create_canvas_size_tables.py` - Database migration script
- `run_canvas_size_migration.py` - Migration runner script
- `server/engine/resizing_with_db.py` - Example of modified resizing.py

### Modified Files
- `server/api/models.py` - Added new models and Pydantic schemas
- `server/api/routes.py` - Added new API endpoints 