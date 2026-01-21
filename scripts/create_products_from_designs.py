#!/usr/bin/env python3
"""
Create Products from Existing Designs

This script finds designs in your database and creates ecommerce products for them.

Usage:
    python create_products_from_designs.py --shop "Funny Bunny"
    python create_products_from_designs.py --template "16oz Tumbler"
    python create_products_from_designs.py --all
"""

import os
import sys
import argparse
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
API_BASE_URL = "https://printer-automation-backend-production.up.railway.app"

# Price mapping by print method
PRICE_MAP = {
    'uvdtf': 3.50,
    'dtf': 4.00,
    'sublimation': 3.00,
    'vinyl': 2.50,
    'digital': 1.99
}

def get_designs(shop=None, template=None):
    """Fetch designs from database"""
    engine = create_engine(DATABASE_URL)

    query = """
        SELECT
            id,
            design_name,
            shop_name,
            template_name,
            image_url,
            platform
        FROM design_images
        WHERE 1=1
    """

    params = {}

    if shop:
        query += " AND shop_name = :shop"
        params['shop'] = shop

    if template:
        query += " AND template_name = :template"
        params['template'] = template

    query += " ORDER BY shop_name, template_name, design_name"

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        designs = [dict(row._mapping) for row in result]

    return designs


def create_slug(name):
    """Generate URL-friendly slug"""
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


def determine_print_method(template_name):
    """Guess print method from template name"""
    template = template_name.lower() if template_name else ''

    if 'tumbler' in template or 'cup' in template:
        return 'uvdtf'
    elif 'shirt' in template or 'tshirt' in template:
        return 'dtf'
    elif 'mug' in template:
        return 'sublimation'
    else:
        return 'uvdtf'  # Default


def determine_category(template_name):
    """Guess category from template name"""
    template = template_name.lower() if template_name else ''

    if 'tumbler' in template or 'cup' in template:
        return 'cup_wraps'
    elif 'square' in template:
        return 'single_square'
    elif 'rect' in template or 'rectangle' in template:
        return 'single_rectangle'
    else:
        return 'other'


def create_product_from_design(design, dry_run=False):
    """Create ecommerce product from design"""

    print_method = determine_print_method(design['template_name'])
    category = determine_category(design['template_name'])
    price = PRICE_MAP.get(print_method, 3.50)

    product_data = {
        "name": design['design_name'],
        "slug": create_slug(design['design_name']),
        "description": f"{design['design_name']} - {design['template_name']}",
        "short_description": f"High quality {print_method.upper()} design",
        "product_type": "physical",
        "print_method": print_method,
        "category": category,
        "price": price,
        "compare_at_price": price * 1.5,  # 50% markup
        "track_inventory": False,  # Made to order
        "inventory_quantity": 999,
        "allow_backorder": True,
        "images": [design['image_url']] if design['image_url'] else [],
        "featured_image": design['image_url'],
        "is_active": True,
        "is_featured": False,
        "design_id": str(design['id']),
        "template_name": design['template_name']
    }

    if dry_run:
        print(f"  [DRY RUN] Would create: {product_data['name']}")
        return True

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/ecommerce/products/",
            json=product_data
        )
        response.raise_for_status()
        product = response.json()
        print(f"  ✅ Created: {product['name']} (${product['price']})")
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and 'duplicate' in str(e.response.text).lower():
            print(f"  ⚠️  Skipped (already exists): {product_data['name']}")
            return True
        print(f"  ❌ Failed: {product_data['name']} - {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {product_data['name']} - {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Create products from existing designs')
    parser.add_argument('--shop', help='Filter by shop name')
    parser.add_argument('--template', help='Filter by template name')
    parser.add_argument('--all', action='store_true', help='Process all designs')
    parser.add_argument('--dry-run', action='store_true', help='Preview without creating')
    parser.add_argument('--limit', type=int, help='Limit number of products to create')

    args = parser.parse_args()

    if not any([args.shop, args.template, args.all]):
        parser.print_help()
        sys.exit(1)

    print("🔍 Fetching designs from database...\n")
    designs = get_designs(shop=args.shop, template=args.template)

    if not designs:
        print("❌ No designs found matching criteria")
        sys.exit(1)

    print(f"📦 Found {len(designs)} designs\n")

    if args.limit:
        designs = designs[:args.limit]
        print(f"   Processing first {args.limit} designs\n")

    created = 0
    failed = 0

    for design in designs:
        if create_product_from_design(design, dry_run=args.dry_run):
            created += 1
        else:
            failed += 1

    print(f"\n📊 Summary:")
    print(f"   ✅ Created: {created}")
    print(f"   ❌ Failed: {failed}")

    if args.dry_run:
        print(f"\n💡 This was a dry run. Remove --dry-run to actually create products.")


if __name__ == "__main__":
    main()
