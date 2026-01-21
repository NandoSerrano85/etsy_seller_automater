#!/usr/bin/env python3
"""
Quick diagnostic script to test CraftFlow Commerce admin API routes
"""
import sys
import os

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

print("=" * 60)
print("Testing CraftFlow Commerce Admin API Routes")
print("=" * 60)

# Test health endpoint first
print("\n1. Testing Health Endpoint...")
response = client.get("/health")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")

# Test admin routes (without auth - should get 401)
admin_routes = [
    "/api/ecommerce/admin/products/",
    "/api/ecommerce/admin/orders/",
    "/api/ecommerce/admin/customers/",
    "/api/ecommerce/admin/storefront-settings/",
]

print("\n2. Testing Admin Routes (expecting 401 without auth)...")
for route in admin_routes:
    response = client.get(route)
    status = "✅" if response.status_code == 401 else "❌"
    print(f"   {status} {route}")
    print(f"      Status: {response.status_code}")
    if response.status_code != 401:
        print(f"      Response: {response.text[:100]}")

# Test public endpoint
print("\n3. Testing Public Storefront Settings Endpoint...")
response = client.get("/api/ecommerce/admin/storefront-settings/public/1")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✅ Public endpoint working")
    print(f"   Response: {response.json()}")
else:
    print(f"   ❌ Public endpoint failed")
    print(f"   Response: {response.text[:200]}")

# List all registered routes
print("\n4. Registered Routes with 'admin' in path:")
print("   " + "-" * 56)
for route in app.routes:
    if hasattr(route, 'path') and 'admin' in route.path.lower():
        methods = getattr(route, 'methods', ['N/A'])
        print(f"   {', '.join(methods):8} {route.path}")

print("\n" + "=" * 60)
print("Diagnostic Complete")
print("=" * 60)
