#!/usr/bin/env python3
"""
Bulk Product Upload Script for Ecommerce Storefront

Usage:
    python upload_products.py products.csv

CSV Format:
name,slug,description,short_description,product_type,print_method,category,price,compare_at_price,inventory_quantity,image_url,is_featured
"""

import csv
import json
import requests
import sys
from pathlib import Path

# Configuration
API_BASE_URL = "https://printer-automation-backend-production.up.railway.app"
# For local testing, use: "http://localhost:3003"

def create_product(product_data):
    """Create a single product via API"""
    url = f"{API_BASE_URL}/api/ecommerce/products/"

    try:
        response = requests.post(url, json=product_data)
        response.raise_for_status()
        product = response.json()
        print(f"✅ Created: {product['name']} (ID: {product['id']})")
        return product
    except requests.exceptions.HTTPError as e:
        print(f"❌ Failed to create {product_data['name']}: {e}")
        if e.response is not None:
            print(f"   Error details: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Error creating {product_data['name']}: {e}")
        return None


def upload_from_csv(csv_file):
    """Upload products from CSV file"""

    if not Path(csv_file).exists():
        print(f"❌ File not found: {csv_file}")
        return

    products_created = 0
    products_failed = 0

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Build product data from CSV row
            product_data = {
                "name": row['name'],
                "slug": row['slug'],
                "description": row.get('description', ''),
                "short_description": row.get('short_description', ''),
                "product_type": row.get('product_type', 'physical'),
                "print_method": row.get('print_method', 'uvdtf'),
                "category": row.get('category', 'cup_wraps'),
                "price": float(row['price']),
                "compare_at_price": float(row['compare_at_price']) if row.get('compare_at_price') else None,
                "track_inventory": row.get('track_inventory', 'true').lower() == 'true',
                "inventory_quantity": int(row.get('inventory_quantity', 0)),
                "allow_backorder": row.get('allow_backorder', 'false').lower() == 'true',
                "images": [row['image_url']] if row.get('image_url') else [],
                "featured_image": row.get('image_url'),
                "is_active": row.get('is_active', 'true').lower() == 'true',
                "is_featured": row.get('is_featured', 'false').lower() == 'true',
            }

            if create_product(product_data):
                products_created += 1
            else:
                products_failed += 1

    print(f"\n📊 Summary:")
    print(f"   ✅ Created: {products_created}")
    print(f"   ❌ Failed: {products_failed}")


def upload_from_json(json_file):
    """Upload products from JSON file"""

    if not Path(json_file).exists():
        print(f"❌ File not found: {json_file}")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    products_created = 0
    products_failed = 0

    for product_data in products:
        if create_product(product_data):
            products_created += 1
        else:
            products_failed += 1

    print(f"\n📊 Summary:")
    print(f"   ✅ Created: {products_created}")
    print(f"   ❌ Failed: {products_failed}")


def create_sample_csv():
    """Create a sample CSV file"""
    sample_file = "sample_products.csv"

    with open(sample_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'name', 'slug', 'description', 'short_description', 'product_type',
            'print_method', 'category', 'price', 'compare_at_price',
            'inventory_quantity', 'image_url', 'is_featured'
        ])
        writer.writerow([
            'Funny Bunny Cup Wrap',
            'funny-bunny-cup-wrap',
            'High quality UV DTF cup wrap with funny bunny design',
            'Cute bunny design for 16oz cups',
            'physical',
            'uvdtf',
            'cup_wraps',
            '3.50',
            '5.00',
            '100',
            'https://example.com/bunny.jpg',
            'true'
        ])
        writer.writerow([
            'Christmas Tree Cup Wrap',
            'christmas-tree-cup-wrap',
            'Festive Christmas tree design',
            'Perfect for holiday season',
            'physical',
            'uvdtf',
            'cup_wraps',
            '3.50',
            '',
            '50',
            'https://example.com/tree.jpg',
            'false'
        ])

    print(f"✅ Created sample CSV: {sample_file}")
    print(f"   Edit this file and run: python upload_products.py {sample_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python upload_products.py products.csv")
        print("  python upload_products.py products.json")
        print("  python upload_products.py --create-sample")
        sys.exit(1)

    file_path = sys.argv[1]

    if file_path == "--create-sample":
        create_sample_csv()
    elif file_path.endswith('.csv'):
        print(f"📦 Uploading products from CSV: {file_path}\n")
        upload_from_csv(file_path)
    elif file_path.endswith('.json'):
        print(f"📦 Uploading products from JSON: {file_path}\n")
        upload_from_json(file_path)
    else:
        print("❌ Unsupported file format. Use .csv or .json")
        sys.exit(1)
