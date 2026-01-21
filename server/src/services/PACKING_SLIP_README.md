# Packing Slip Generator

Professional packing slip PDF generator for orders with product mockups, customer information, and order summary.

## Features

✅ **Professional Layout**

- Shop name and order info header
- Customer shipping information
- Product mockup thumbnails in grid layout (1" spacing)
- Large, bold quantity display under each product
- Detailed order summary table at bottom
- Fits on 8.5" x 11" paper

✅ **Automatic Pagination**

- Handles multiple products across pages
- Summary table always appears on last page
- Maintains consistent formatting

✅ **Customizable**

- Supports custom shop names
- Flexible customer address formats
- Optional order numbers and dates
- Product images from URLs

## API Endpoints

### Generate Packing Slip

**POST** `/api/packing-slip/generate`

Generate and download a packing slip PDF.

**Request Body:**

```json
{
  "shop_name": "Your Shop Name",
  "order_number": "ORD-12345",
  "order_date": "January 1, 2025",
  "customer": {
    "name": "John Doe",
    "email": "john@example.com",
    "address": {
      "line1": "123 Main Street",
      "line2": "Apt 4B",
      "city": "New York",
      "state": "NY",
      "zip": "10001",
      "country": "USA"
    }
  },
  "items": [
    {
      "name": "Custom T-Shirt",
      "mockup_url": "https://example.com/image.jpg",
      "quantity": 2,
      "price": 24.99
    }
  ],
  "subtotal": 49.98,
  "shipping_cost": 8.5,
  "total": 58.48
}
```

**Response:**

- Content-Type: `application/pdf`
- Downloads as: `packing_slip_{order_number}.pdf`

### Preview Packing Slip

**POST** `/api/packing-slip/preview`

Generate a packing slip for inline viewing (no download).

Same request body as `/generate`, but opens in browser instead of downloading.

### Sample Packing Slip

**GET** `/api/packing-slip/sample`

Generate a sample packing slip with placeholder data (no authentication required).

Perfect for testing and seeing the layout.

## Usage Examples

### Frontend (JavaScript/React)

```javascript
// Generate packing slip
const generatePackingSlip = async (orderData) => {
  const response = await fetch("/api/packing-slip/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(orderData),
  });

  // Download the PDF
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `packing_slip_${orderData.order_number}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
};

// Preview in new tab
const previewPackingSlip = async (orderData) => {
  const response = await fetch("/api/packing-slip/preview", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(orderData),
  });

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  window.open(url, "_blank");
};

// Example order data
const orderData = {
  shop_name: "Funny Bunny Transfers",
  order_number: "12345",
  order_date: "January 8, 2025",
  customer: {
    name: "Jane Smith",
    email: "jane@example.com",
    address: {
      line1: "456 Oak Avenue",
      city: "Los Angeles",
      state: "CA",
      zip: "90001",
      country: "USA",
    },
  },
  items: [
    {
      name: "Custom Hoodie",
      mockup_url: "https://example.com/mockup1.jpg",
      quantity: 2,
      price: 39.99,
    },
    {
      name: "T-Shirt Design",
      mockup_url: "https://example.com/mockup2.jpg",
      quantity: 3,
      price: 24.99,
    },
  ],
  subtotal: 154.95,
  shipping_cost: 12.0,
  total: 166.95,
};

// Generate the packing slip
generatePackingSlip(orderData);
```

### Python

```python
import requests

# Order data
order_data = {
    "shop_name": "My Shop",
    "order_number": "ORD-123",
    "customer": {
        "name": "Customer Name",
        "email": "customer@example.com",
        "address": {
            "line1": "123 Street",
            "city": "City",
            "state": "ST",
            "zip": "12345"
        }
    },
    "items": [
        {
            "name": "Product 1",
            "mockup_url": "https://example.com/image.jpg",
            "quantity": 2,
            "price": 25.00
        }
    ],
    "subtotal": 50.00,
    "shipping_cost": 5.00,
    "total": 55.00
}

# Generate packing slip
response = requests.post(
    "http://localhost:3003/api/packing-slip/generate",
    json=order_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

# Save PDF
with open("packing_slip.pdf", "wb") as f:
    f.write(response.content)
```

### cURL

```bash
# Test with sample packing slip (no auth needed)
curl -o sample.pdf http://localhost:3003/api/packing-slip/sample

# Generate with custom data
curl -X POST http://localhost:3003/api/packing-slip/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "shop_name": "My Shop",
    "customer": {
      "name": "John Doe",
      "address": "123 Main St, City, ST 12345"
    },
    "items": [
      {
        "name": "Product",
        "quantity": 1,
        "price": 25.00
      }
    ],
    "subtotal": 25.00,
    "shipping_cost": 5.00,
    "total": 30.00
  }' \
  -o packing_slip.pdf
```

## Layout Specifications

### Header Section

- **Shop Name**: Large, centered, 24pt font
- **Order Info**: Order number and date, centered below shop name

### Customer Information

- **Label**: "Ship To:" in bold
- **Name**: Bold, prominent
- **Email**: Below name
- **Address**: Multi-line, formatted

### Product Grid

- **Thumbnail Size**: 2.5" x 2.5"
- **Spacing**: 1" between images
- **Columns**: 1-3 (auto-calculated based on paper width)
- **Quantity Display**: Large (16pt), bold, red color, centered under image

### Order Summary Table

- **Location**: Bottom of last page
- **Columns**: Item, Quantity, Price, Total
- **Rows**:
  - Each product with price calculation
  - Subtotal
  - Shipping cost
  - Total (bold, highlighted)

### Page Dimensions

- **Paper Size**: 8.5" x 11" (US Letter)
- **Margins**: 0.5" on all sides
- **Content Area**: 7.5" x 10"

## Customization

### Custom Styles

To customize the packing slip appearance, edit `/server/src/services/packing_slip_generator.py`:

```python
# Change shop name color
self.styles.add(ParagraphStyle(
    name='ShopName',
    parent=self.styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor('#YOUR_COLOR'),  # Change this
    spaceAfter=12,
    alignment=TA_CENTER
))

# Change quantity color
self.styles.add(ParagraphStyle(
    name='Quantity',
    parent=self.styles['Normal'],
    fontSize=16,
    fontName='Helvetica-Bold',
    textColor=colors.HexColor('#YOUR_COLOR'),  # Change this
    alignment=TA_CENTER
))
```

### Custom Thumbnail Size

```python
# In _create_product_grid method
thumbnail_size = 2.5 * inch  # Change this value
```

### Custom Spacing

```python
# In __init__ method
self.thumbnail_spacing = 1 * inch  # Change spacing between images
self.margin = 0.5 * inch  # Change page margins
```

## Testing

### Generate Sample

```bash
# Quick test - generate sample PDF
curl -o test.pdf http://localhost:3003/api/packing-slip/sample

# Open the PDF
open test.pdf  # macOS
xdg-open test.pdf  # Linux
start test.pdf  # Windows
```

### Unit Test

```python
from server.src.services.packing_slip_generator import generate_sample_packing_slip

# Run the generator
generate_sample_packing_slip()
# Creates: sample_packing_slip.pdf
```

## Troubleshooting

### Images Not Loading

If product mockup images don't appear:

1. Check image URLs are publicly accessible
2. Verify images are in supported formats (JPG, PNG)
3. Check firewall/network settings
4. Images must be downloadable via HTTP/HTTPS

**Fallback**: If image fails to load, product name is displayed as placeholder text.

### PDF Not Downloading

1. Check authentication token is valid
2. Verify all required fields are provided
3. Check browser console for errors
4. Try the `/sample` endpoint first to verify service is working

### Layout Issues

1. **Too many products**: Grid automatically handles pagination
2. **Long product names**: Names are truncated to 40 characters in summary table
3. **Missing data**: Optional fields default to sensible values

## Dependencies

- **reportlab**: PDF generation library
- **requests**: For downloading product images
- **Pillow**: Image processing (via reportlab)

Install with:

```bash
pip install reportlab==4.0.7
```

## Security Notes

- Authentication required for `/generate` and `/preview` endpoints
- Product image URLs are fetched server-side
- No user data is stored - PDFs generated on-the-fly
- 10-second timeout on image downloads

## Performance

- **Generation Time**: ~1-2 seconds for typical orders
- **File Size**: 50-500KB depending on number of product images
- **Concurrent Requests**: Handles multiple simultaneous generations
- **Memory Usage**: ~10-20MB per generation

## Support

For issues or questions:

1. Check this README
2. Test with `/sample` endpoint
3. Verify request data format matches examples
4. Check server logs for detailed error messages
