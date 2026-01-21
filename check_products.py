#!/usr/bin/env python3
"""
Quick diagnostic to check product status in database
"""
import requests
import json

API_URL = "https://printer-automation-backend-production.up.railway.app"

print("=" * 60)
print("Product Diagnostic Check")
print("=" * 60)

# Test health
print("\n1. Testing backend health...")
try:
    r = requests.get(f"{API_URL}/health")
    print(f"   ✅ Backend health: {r.status_code}")
except Exception as e:
    print(f"   ❌ Backend health failed: {e}")
    exit(1)

# Test storefront products endpoint
print("\n2. Testing storefront products API...")
try:
    r = requests.get(f"{API_URL}/api/storefront/products")
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Response type: {type(data)}")
        if isinstance(data, dict):
            print(f"   Total products: {data.get('total', 'N/A')}")
            print(f"   Items returned: {len(data.get('items', []))}")
            print(f"   Page: {data.get('page', 'N/A')}")
            print(f"   Page size: {data.get('page_size', 'N/A')}")

            if data.get('items'):
                print("\n   Products found:")
                for product in data['items'][:5]:  # Show first 5
                    print(f"      - {product.get('name')} (active: {product.get('is_active')}, slug: {product.get('slug')})")
            else:
                print("   ⚠️  No products in response")
        else:
            print(f"   ⚠️  Unexpected response format: {data}")
    else:
        print(f"   ❌ Error: {r.text[:200]}")
except Exception as e:
    print(f"   ❌ Request failed: {e}")

# Test a specific product by slug if we have one
print("\n3. Checking if routes are registered...")
try:
    r = requests.get(f"{API_URL}/openapi.json")
    if r.status_code == 200:
        openapi = r.json()
        paths = openapi.get('paths', {})
        storefront_routes = [p for p in paths.keys() if 'storefront' in p]
        print(f"   Found {len(storefront_routes)} storefront routes:")
        for route in storefront_routes[:10]:
            print(f"      - {route}")
    else:
        print(f"   ❌ Could not get OpenAPI spec: {r.status_code}")
except Exception as e:
    print(f"   ❌ OpenAPI check failed: {e}")

print("\n" + "=" * 60)
print("Diagnostic Complete")
print("=" * 60)
