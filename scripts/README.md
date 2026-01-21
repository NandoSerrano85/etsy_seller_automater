# Product Upload Scripts

Scripts for managing products in your ecommerce storefront.

## Prerequisites

Install required dependencies:

```bash
pip install requests python-dotenv sqlalchemy psycopg2-binary
```

## Method 1: Upload from CSV/JSON

Create products from a CSV or JSON file.

### Create Sample CSV

```bash
python upload_products.py --create-sample
```

This creates `sample_products.csv` with example data. Edit it with your products.

### Upload from CSV

```bash
python upload_products.py products.csv
```

### CSV Format

```csv
name,slug,description,short_description,product_type,print_method,category,price,compare_at_price,inventory_quantity,image_url,is_featured
Funny Bunny Cup Wrap,funny-bunny-cup-wrap,High quality design,Cute bunny design,physical,uvdtf,cup_wraps,3.50,5.00,100,https://example.com/bunny.jpg,true
```

### Upload from JSON

```bash
python upload_products.py products.json
```

JSON format:

```json
[
  {
    "name": "Product Name",
    "slug": "product-slug",
    "description": "Full description",
    "short_description": "Short description",
    "product_type": "physical",
    "print_method": "uvdtf",
    "category": "cup_wraps",
    "price": 3.5,
    "images": ["https://image-url.jpg"],
    "is_active": true
  }
]
```

## Method 2: Create from Existing Designs

Convert your existing designs in the database to products.

### Preview (Dry Run)

```bash
python create_products_from_designs.py --shop "Funny Bunny" --dry-run
```

### Create Products from All Designs

```bash
python create_products_from_designs.py --all
```

### Filter by Shop

```bash
python create_products_from_designs.py --shop "Funny Bunny"
```

### Filter by Template

```bash
python create_products_from_designs.py --template "16oz Tumbler"
```

### Limit Number of Products

```bash
python create_products_from_designs.py --all --limit 10
```

## Product Fields

### Required Fields

- `name` - Product name
- `slug` - URL-friendly identifier (must be unique)
- `product_type` - "physical" or "digital"
- `print_method` - "uvdtf", "dtf", "sublimation", "vinyl", "other", or "digital"
- `category` - "cup_wraps", "single_square", "single_rectangle", or "other"
- `price` - Product price (must be > 0)

### Optional Fields

- `description` - Full product description
- `short_description` - Brief description (max 500 chars)
- `compare_at_price` - Original price (for showing discounts)
- `cost` - Your cost (for margin tracking)
- `track_inventory` - true/false (default: false)
- `inventory_quantity` - Stock quantity (default: 0)
- `allow_backorder` - Allow sales when out of stock (default: false)
- `digital_file_url` - Download URL for digital products
- `images` - Array of image URLs
- `featured_image` - Main product image URL
- `is_active` - Show on storefront (default: true)
- `is_featured` - Show in featured section (default: false)
- `design_id` - Link to design_images table
- `template_name` - Template used for design

## Print Methods

- `uvdtf` - UV DTF transfers
- `dtf` - DTF transfers
- `sublimation` - Sublimation prints
- `vinyl` - Vinyl decals
- `digital` - Digital downloads
- `other` - Other methods

## Categories

- `cup_wraps` - Cup/tumbler wraps
- `single_square` - Single square designs
- `single_rectangle` - Single rectangular designs
- `other` - Other custom products
