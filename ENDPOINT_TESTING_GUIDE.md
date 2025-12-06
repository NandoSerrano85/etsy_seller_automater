# 🧪 Endpoint Testing Guide - Etsy Seller Automator

This guide will help you test all endpoints in your application to establish baseline performance metrics and verify optimizations.

---

## 📋 Prerequisites

1. **Get Your Authentication Token:**
   - Login to your application at: https://printer-automation-frontend-production.up.railway.app
   - Open browser DevTools (F12)
   - Go to Application/Storage → Local Storage
   - Find and copy your `access_token`

2. **Install Testing Tools:**

   ```bash
   # Option 1: Using curl (built-in on Mac/Linux)
   curl --version

   # Option 2: Using HTTPie (recommended - more user-friendly)
   pip install httpie

   # Option 3: Using Postman (GUI)
   # Download from: https://www.postman.com/downloads/
   ```

3. **Set Environment Variables (optional but recommended):**
   ```bash
   export API_URL="https://printer-automation-frontend-production.up.railway.app"
   export AUTH_TOKEN="your_access_token_here"
   ```

---

## 🏥 Health Check Endpoints (No Auth Required)

These endpoints check if the API is running and healthy.

### 1. Basic Health Check

```bash
# Using curl
curl -i "$API_URL/health"

# Using HTTPie
http GET "$API_URL/health"

# Expected Response:
{
  "status": "healthy",
  "timestamp": 1733428800,
  "version": "1.0.0",
  "environment": "production"
}
```

**Expected Time:** < 100ms

---

### 2. Detailed Health Check

```bash
# Using curl
curl -i "$API_URL/health/detailed"

# Using HTTPie
http GET "$API_URL/health/detailed"

# Expected Response:
{
  "status": "healthy",
  "timestamp": 1733428800,
  "version": "1.0.0",
  "environment": "production",
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 62.5,
    "memory_available": 1234567890,
    "disk_percent": 55.3,
    "disk_free": 9876543210
  },
  "services": {
    "database": "healthy",
    "api": "healthy"
  }
}
```

**Expected Time:** 100-300ms

---

### 3. Ping & Ready

```bash
# Ping
curl -i "$API_URL/ping"

# Ready (for Railway health checks)
curl -i "$API_URL/ready"
```

**Expected Time:** < 50ms

---

## 🔐 Authentication & User Endpoints

### 4. Get Current User Info

```bash
# Using curl
curl -i -H "Authorization: Bearer $AUTH_TOKEN" "$API_URL/users/me"

# Using HTTPie
http GET "$API_URL/users/me" "Authorization: Bearer $AUTH_TOKEN"

# Expected Response:
{
  "id": "uuid-here",
  "email": "your@email.com",
  "shop_name": "YourShopName",
  "etsy_shop_id": "12345678",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Expected Time:** 100-300ms
**⚠️ If this fails:** Your token is expired or invalid. Re-login to get a new token.

---

## 📊 Dashboard Endpoints (These are the ones we're optimizing!)

### 5. Monthly Analytics (⏱️ BASELINE TEST - Track this!)

```bash
# Current year analytics
curl -i -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/dashboard/analytics?year=2025" \
  -w "\nTime: %{time_total}s\n"

# Using HTTPie with timing
time http GET "$API_URL/dashboard/analytics?year=2025" \
  "Authorization: Bearer $AUTH_TOKEN"

# Expected Response:
{
  "year": 2025,
  "summary": {
    "total_sales": 15234.50,
    "total_quantity": 1523,
    "total_discounts": 234.50,
    "net_sales": 15000.00,
    "total_receipts": 456
  },
  "monthly_breakdown": [
    {
      "month": 1,
      "month_name": "January",
      "total_sales": 1234.50,
      "total_quantity": 123,
      "receipt_count": 45,
      "top_items": [...]
    },
    // ... 11 more months
  ],
  "year_top_sellers": [...]
}
```

**⏱️ BEFORE OPTIMIZATION:** 15-30 seconds
**⏱️ AFTER PHASE 1:** 5-10 seconds
**⏱️ AFTER PHASE 2:** 3-5 seconds
**⏱️ AFTER PHASE 3:** < 1 second

**💡 Test Strategy:**

```bash
# Test 1: First call (cache miss - should be slow)
echo "Test 1: First call (cache miss)"
time curl -H "Authorization: Bearer $AUTH_TOKEN" "$API_URL/dashboard/analytics?year=2025"

# Test 2: Second call immediately (cache hit - should be fast)
echo "\nTest 2: Second call (cache hit)"
time curl -H "Authorization: Bearer $AUTH_TOKEN" "$API_URL/dashboard/analytics?year=2025"

# Test 3: Different year (cache miss again)
echo "\nTest 3: Different year"
time curl -H "Authorization: Bearer $AUTH_TOKEN" "$API_URL/dashboard/analytics?year=2024"
```

---

### 6. Top Sellers

```bash
curl -i -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/dashboard/top-sellers?year=2025" \
  -w "\nTime: %{time_total}s\n"

# Expected Response:
{
  "year": 2025,
  "top_sellers": [
    {
      "listing_id": 123456789,
      "title": "Custom UV DTF Transfer",
      "quantity_sold": 245,
      "total_amount": 2450.00,
      "total_discounts": 50.00,
      "net_amount": 2400.00
    },
    // ... more items
  ],
  "total_items": 50
}
```

**Expected Time:** Similar to analytics (15-30 seconds before optimization)

---

### 7. Shop Listings

```bash
curl -i -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/dashboard/shop-listings?limit=50&offset=0" \
  -w "\nTime: %{time_total}s\n"

# Expected Response:
{
  "designs": [
    {
      "listing_id": 123456789,
      "title": "Custom Design Name",
      "description": "Description here",
      "price": 10.00,
      "quantity": 999,
      "state": "active",
      "images": [
        {
          "url_full": "https://...",
          "url_75": "https://...",
          "url_170": "https://..."
        }
      ]
    }
  ],
  "count": 50,
  "total": 234,
  "pagination": {
    "limit": 50,
    "offset": 0
  }
}
```

**Expected Time:** 3-8 seconds

---

## 📦 Orders Endpoints (Also being optimized!)

### 8. Get Active Orders (⏱️ BASELINE TEST)

```bash
# Active orders (paid, not shipped)
curl -i -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/orders?was_paid=true&was_shipped=false&was_canceled=false" \
  -w "\nTime: %{time_total}s\n"

# Expected Response:
{
  "orders": [
    {
      "order_id": 1234567890,
      "order_date": 1733428800,
      "shipping_method": "USPS",
      "shipping_cost": 5.50,
      "customer_name": "John Doe",
      "items": [
        {
          "title": "Custom Transfer",
          "quantity": 2,
          "price": 10.00,
          "listing_id": 123456789
        }
      ]
    }
  ],
  "count": 10,
  "total": 10
}
```

**Expected Time:** 3-5 seconds

---

### 9. Get All Orders (Paginated)

```bash
curl -i -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/orders/all-orders?limit=100&offset=0" \
  -w "\nTime: %{time_total}s\n"

# Test pagination
curl -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/orders/all-orders?limit=50&offset=50"
```

**Expected Time:** 5-8 seconds for 100 orders

---

### 10. Get Shipped Orders

```bash
curl -i -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/orders?was_paid=true&was_shipped=true&was_canceled=false" \
  -w "\nTime: %{time_total}s\n"
```

---

## 🖨️ Print File / Gangsheet Endpoints (⏱️ BIGGEST OPTIMIZATION)

### 11. Create Print Files from All Active Orders (⏱️ BASELINE TEST)

```bash
# This is the SLOWEST endpoint - generates gangsheets
curl -X POST -i -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  "$API_URL/orders/print-files" \
  -w "\nTime: %{time_total}s\n"

# Expected Response:
{
  "success": true,
  "message": "Print files created successfully - 3 sheets generated",
  "sheets_created": 3,
  "uploaded_files": [
    "UVDTF_16oz_gangsheet_1_2025-12-05.png",
    "UVDTF_16oz_gangsheet_2_2025-12-05.png",
    "UVDTF_16oz_gangsheet_3_2025-12-05.png"
  ],
  "storage_mode": "NAS"
}
```

**⏱️ BEFORE OPTIMIZATION:** 40-90 seconds (depends on # of designs)
**⏱️ AFTER PHASE 2:** 10-20 seconds
**⏱️ AFTER PHASE 3:** 5-10 seconds

**⚠️ WARNING:** This endpoint:

- Downloads designs from NAS
- Generates gang sheet images
- Uploads results back to NAS
- Can take 1-2 minutes with many orders

---

### 12. Create Print Files from Mockups (Database-based)

```bash
curl -X POST -i -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "UVDTF 16oz"
  }' \
  "$API_URL/orders/print-files-from-mockups" \
  -w "\nTime: %{time_total}s\n"
```

**Expected Time:** 20-60 seconds

---

### 13. Create Print Files from Selected Orders

```bash
curl -X POST -i -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_ids": [1234567890, 1234567891],
    "template_name": "UVDTF 16oz"
  }' \
  "$API_URL/orders/selected-orders/print-files" \
  -w "\nTime: %{time_total}s\n"
```

**Expected Time:** 15-45 seconds (depends on # of orders)

---

## 🎨 Design Endpoints

### 14. Get Designs

```bash
curl -i -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/designs" \
  -w "\nTime: %{time_total}s\n"
```

**Expected Time:** 1-3 seconds

---

### 15. Upload Designs (Multipart)

```bash
# This is more complex - typically done via frontend
# Example for testing:
curl -X POST -i -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "files=@/path/to/design.png" \
  "$API_URL/designs/start-upload"
```

---

## 🖼️ Mockup Endpoints

### 16. Get Mockups

```bash
curl -i -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/mockups" \
  -w "\nTime: %{time_total}s\n"
```

---

### 17. Create Mockup

```bash
curl -X POST -i -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "design_id": "design-uuid-here",
    "template_name": "UVDTF 16oz"
  }' \
  "$API_URL/mockups/create"
```

---

## 🔗 OAuth & Connection Endpoints

### 18. Check OAuth Token Status

```bash
curl -i -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/oauth-tokens/status"

# Expected Response:
{
  "connected": true,
  "provider": "etsy",
  "expires_at": "2025-12-05T10:00:00Z",
  "is_expired": false
}
```

---

### 19. Platform Connections

```bash
curl -i -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/platform-connections"
```

---

## 🛒 Shopify Endpoints (if applicable)

### 20. Shopify Products

```bash
curl -i -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/shopify/products?limit=50"
```

---

### 21. Shopify Orders

```bash
curl -i -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_URL/shopify/orders?limit=50"
```

---

## 📄 Packing Slip Endpoint

### 22. Generate Packing Slip PDF

```bash
curl -X POST -i -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "1234567890"
  }' \
  "$API_URL/api/packing-slip/generate" \
  --output packing_slip.pdf
```

---

## 🧪 Complete Test Suite Script

Save this as `test_all_endpoints.sh`:

```bash
#!/bin/bash

# Configuration
API_URL="https://printer-automation-frontend-production.up.railway.app"
AUTH_TOKEN="your_token_here"  # REPLACE THIS

echo "🧪 Starting Endpoint Test Suite"
echo "================================"
echo ""

# Helper function
test_endpoint() {
  local name=$1
  local method=$2
  local endpoint=$3
  local data=$4

  echo "Testing: $name"
  echo "Endpoint: $method $endpoint"

  start_time=$(date +%s.%N)

  if [ "$method" = "GET" ]; then
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      "$API_URL$endpoint")
  else
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
      -X POST \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$data" \
      "$API_URL$endpoint")
  fi

  end_time=$(date +%s.%N)
  duration=$(echo "$end_time - $start_time" | bc)

  http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)

  echo "⏱️  Time: ${duration}s"
  echo "📊 Status: $http_code"
  echo "---"
  echo ""
}

# Health checks
echo "🏥 HEALTH CHECKS"
test_endpoint "Basic Health" "GET" "/health"
test_endpoint "Detailed Health" "GET" "/health/detailed"
test_endpoint "Ping" "GET" "/ping"

# Dashboard (KEY PERFORMANCE METRICS)
echo "📊 DASHBOARD ENDPOINTS (KEY METRICS)"
test_endpoint "Analytics 2025 - First Call" "GET" "/dashboard/analytics?year=2025"
test_endpoint "Analytics 2025 - Second Call (Cache)" "GET" "/dashboard/analytics?year=2025"
test_endpoint "Top Sellers 2025" "GET" "/dashboard/top-sellers?year=2025"
test_endpoint "Shop Listings" "GET" "/dashboard/shop-listings?limit=50"

# Orders (KEY PERFORMANCE METRICS)
echo "📦 ORDERS ENDPOINTS (KEY METRICS)"
test_endpoint "Active Orders" "GET" "/orders?was_paid=true&was_shipped=false"
test_endpoint "All Orders" "GET" "/orders/all-orders?limit=100&offset=0"

# Print Files (SLOWEST ENDPOINTS)
echo "🖨️ PRINT FILE ENDPOINTS (SLOWEST - BE PATIENT)"
# Uncomment these if you want to test (they're slow and create real files)
# test_endpoint "Create Print Files from Active Orders" "POST" "/orders/print-files"

echo ""
echo "✅ Test Suite Complete!"
echo "================================"
```

**To run:**

```bash
chmod +x test_all_endpoints.sh
./test_all_endpoints.sh
```

---

## 📊 Performance Tracking Template

Create a spreadsheet or text file to track performance before/after:

```
ENDPOINT PERFORMANCE TRACKING
============================

Date: 2025-12-05
Version: BEFORE OPTIMIZATION

| Endpoint                      | First Call | Cache Hit | Notes          |
|-------------------------------|------------|-----------|----------------|
| /health                       | 50ms       | N/A       | Always fast    |
| /dashboard/analytics (2025)   | 23.5s      | 0.8s      | NEEDS FIX      |
| /dashboard/top-sellers (2025) | 18.2s      | 0.7s      | NEEDS FIX      |
| /orders (active)              | 4.3s       | 0.5s      | OK             |
| /orders/all-orders (100)      | 6.8s       | 0.6s      | OK             |
| /orders/print-files           | 52.3s      | N/A       | VERY SLOW      |

---

Date: 2025-12-05
Version: AFTER PHASE 1

| Endpoint                      | First Call | Cache Hit | Improvement    |
|-------------------------------|------------|-----------|----------------|
| /dashboard/analytics (2025)   | 8.2s       | 0.3s      | -65%           |
| /dashboard/top-sellers (2025) | 7.1s       | 0.3s      | -61%           |
| /orders (active)              | 1.2s       | 0.2s      | -72%           |
```

---

## 🎯 Key Endpoints to Monitor

**PRIORITY 1 (Optimize First):**

1. `/dashboard/analytics` - Currently slowest
2. `/orders/print-files` - Generates gangsheets
3. `/dashboard/top-sellers` - Similar to analytics

**PRIORITY 2 (Optimize Second):** 4. `/orders` (all variants) 5. `/orders/all-orders` 6. `/dashboard/shop-listings`

**PRIORITY 3 (Already Fast):** 7. Health checks 8. `/users/me` 9. OAuth status

---

## 💡 Testing Best Practices

1. **Test in Order:**
   - Health checks first (ensure API is up)
   - Authentication second (ensure token works)
   - Then functional endpoints

2. **Test Cache Behavior:**
   - First call = cache miss (slow)
   - Second call = cache hit (fast)
   - Wait for cache expiry, test again

3. **Record Baselines:**
   - Test BEFORE any changes
   - Test AFTER each optimization phase
   - Compare improvements

4. **Test Under Load:**
   - Run multiple requests simultaneously
   - See how API handles concurrent users

5. **Check Error Cases:**
   - Invalid auth token
   - Missing parameters
   - Rate limiting

---

## 🚨 Common Issues & Solutions

**Issue: 401 Unauthorized**

- Solution: Token expired, re-login and get new token

**Issue: 429 Rate Limited**

- Solution: Wait 1 minute, Etsy API has rate limits

**Issue: 504 Timeout**

- Solution: Endpoint taking too long, this is what we're fixing!

**Issue: 500 Internal Server Error**

- Solution: Check Railway logs for stack trace

---

## 📞 Need Help?

If you get unexpected results:

1. Check Railway logs: https://railway.app/
2. Check browser console for frontend errors
3. Verify your auth token is valid
4. Check if Etsy API is having issues

---

**Created:** 2025-12-05
**Last Updated:** 2025-12-05
**Version:** 1.0
