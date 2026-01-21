# 🛒 Custom Ecommerce Platform - Part 3: Frontend, Fulfillment & Launch

_Continuation from ECOMMERCE_PLATFORM_GUIDE_PART2.md_

---

## 🎨 Phase 3: Customer-Facing Storefront (Continued)

### **Step 3.3: Product Catalog Components**

`storefront/src/components/product/ProductCard.jsx`:

```javascript
import React from "react";
import { Link } from "react-router-dom";

export default function ProductCard({ product }) {
  const discountPercent = product.compare_at_price
    ? Math.round(
        ((product.compare_at_price - product.price) /
          product.compare_at_price) *
          100,
      )
    : null;

  return (
    <Link to={`/products/${product.slug}`} className="group">
      <div className="bg-white rounded-lg shadow-md overflow-hidden transition-transform duration-300 group-hover:scale-105">
        {/* Product Image */}
        <div className="relative aspect-square overflow-hidden bg-gray-100">
          <img
            src={product.featured_image || "/placeholder-product.jpg"}
            alt={product.name}
            className="w-full h-full object-cover"
          />
          {product.is_featured && (
            <span className="absolute top-2 left-2 bg-purple-600 text-white px-2 py-1 text-xs font-semibold rounded">
              Featured
            </span>
          )}
          {discountPercent && (
            <span className="absolute top-2 right-2 bg-red-600 text-white px-2 py-1 text-xs font-semibold rounded">
              -{discountPercent}%
            </span>
          )}
        </div>

        {/* Product Info */}
        <div className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 mb-2">
            {product.name}
          </h3>
          <p className="text-sm text-gray-600 line-clamp-2 mb-3">
            {product.short_description}
          </p>

          {/* Pricing */}
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-purple-600">
              ${product.price.toFixed(2)}
            </span>
            {product.compare_at_price && (
              <span className="text-sm text-gray-500 line-through">
                ${product.compare_at_price.toFixed(2)}
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
```

`storefront/src/pages/Products.jsx`:

```javascript
import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import ProductCard from "../components/product/ProductCard";
import { getProducts, searchProducts } from "../services/products";

export default function Products() {
  const [searchParams] = useSearchParams();
  const urlPrintMethod = searchParams.get("print_method");
  const urlCategory = searchParams.get("category");
  const searchQuery = searchParams.get("q");

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    printMethod: urlPrintMethod || "all",
    category: urlCategory || "all",
    sortBy: "featured",
  });

  useEffect(() => {
    fetchProducts();
  }, [filter, urlPrintMethod, urlCategory, searchQuery]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      let data;
      if (searchQuery) {
        data = await searchProducts(searchQuery);
      } else {
        data = await getProducts({
          print_method:
            filter.printMethod === "all" ? null : filter.printMethod,
          category: filter.category === "all" ? null : filter.category,
        });
      }
      setProducts(data);
    } catch (error) {
      console.error("Error fetching products:", error);
    } finally {
      setLoading(false);
    }
  };

  // Print Method filter options (HOW it's made)
  const printMethods = [
    { value: "all", label: "All Print Methods" },
    { value: "uvdtf", label: "UVDTF" },
    { value: "dtf", label: "DTF" },
    { value: "sublimation", label: "Sublimation" },
    { value: "vinyl", label: "Vinyl" },
    { value: "other", label: "Other" },
  ];

  // Product Type filter options (WHAT it is)
  const categories = [
    { value: "all", label: "All Product Types" },
    { value: "cup_wraps", label: "Cup Wraps" },
    { value: "single_square", label: "Single Square" },
    { value: "single_rectangle", label: "Single Rectangle" },
    { value: "other_custom", label: "Other/Custom" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {searchQuery
            ? `Search Results for "${searchQuery}"`
            : "Shop All Products"}
        </h1>
        <p className="text-gray-600">
          Browse our collection of high-quality UVDTF transfers and designs
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-8">
        {/* Print Method Filter (HOW it's made) */}
        <select
          value={filter.printMethod}
          onChange={(e) =>
            setFilter({ ...filter, printMethod: e.target.value })
          }
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          {printMethods.map((method) => (
            <option key={method.value} value={method.value}>
              {method.label}
            </option>
          ))}
        </select>

        {/* Product Type Filter (WHAT it is) */}
        <select
          value={filter.category}
          onChange={(e) => setFilter({ ...filter, category: e.target.value })}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          {categories.map((cat) => (
            <option key={cat.value} value={cat.value}>
              {cat.label}
            </option>
          ))}
        </select>

        {/* Sort Filter */}
        <select
          value={filter.sortBy}
          onChange={(e) => setFilter({ ...filter, sortBy: e.target.value })}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <option value="featured">Featured</option>
          <option value="price-low">Price: Low to High</option>
          <option value="price-high">Price: High to Low</option>
          <option value="newest">Newest</option>
        </select>
      </div>

      {/* Product Grid */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        </div>
      ) : products.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No products found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </div>
  );
}
```

### **Step 3.4: Shopping Cart Store**

`storefront/src/store/cartStore.js`:

```javascript
import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  addToCart as apiAddToCart,
  getCart as apiGetCart,
  updateCartItem,
  removeCartItem,
} from "../services/cart";

const useCartStore = create(
  persist(
    (set, get) => ({
      cart: {
        items: [],
        subtotal: 0,
        itemCount: 0,
      },
      session_id: null,
      isLoading: false,

      // Initialize cart from API
      initCart: async () => {
        try {
          const cartData = await apiGetCart();
          set({
            cart: cartData,
            session_id: cartData.session_id,
          });
        } catch (error) {
          console.error("Error initializing cart:", error);
        }
      },

      // Add item to cart
      addItem: async (product, variantId = null, quantity = 1) => {
        set({ isLoading: true });
        try {
          const result = await apiAddToCart({
            product_id: product.id,
            variant_id: variantId,
            quantity,
          });

          set({
            cart: result.cart,
            session_id: result.cart.session_id,
            isLoading: false,
          });

          return { success: true };
        } catch (error) {
          set({ isLoading: false });
          return { success: false, error: error.message };
        }
      },

      // Update item quantity
      updateQuantity: async (itemId, quantity) => {
        set({ isLoading: true });
        try {
          const result = await updateCartItem(itemId, quantity);
          set({
            cart: result.cart,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          console.error("Error updating cart:", error);
        }
      },

      // Remove item from cart
      removeItem: async (itemId) => {
        set({ isLoading: true });
        try {
          const result = await removeCartItem(itemId);
          set({
            cart: result.cart,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          console.error("Error removing item:", error);
        }
      },

      // Clear cart
      clearCart: () => {
        set({
          cart: {
            items: [],
            subtotal: 0,
            itemCount: 0,
          },
        });
      },
    }),
    {
      name: "cart-storage",
      partialize: (state) => ({
        session_id: state.session_id,
      }),
    },
  ),
);

export default useCartStore;
```

### **Step 3.5: Checkout Page with Stripe**

`storefront/src/pages/Checkout.jsx`:

```javascript
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { loadStripe } from "@stripe/stripe-js";
import { Elements } from "@stripe/react-stripe-js";
import CheckoutForm from "../components/checkout/CheckoutForm";
import useCartStore from "../store/cartStore";
import { initCheckout } from "../services/checkout";

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

export default function Checkout() {
  const navigate = useNavigate();
  const cart = useCartStore((state) => state.cart);
  const [clientSecret, setClientSecret] = useState("");
  const [orderId, setOrderId] = useState("");
  const [totals, setTotals] = useState(null);

  useEffect(() => {
    if (cart.items.length === 0) {
      navigate("/cart");
    }
  }, [cart, navigate]);

  const handleShippingSubmit = async (shippingData) => {
    try {
      const result = await initCheckout(shippingData);
      setClientSecret(result.payment_intent.client_secret);
      setOrderId(result.order_id);
      setTotals(result.totals);
    } catch (error) {
      console.error("Error initializing checkout:", error);
      alert("Failed to initialize checkout");
    }
  };

  const appearance = {
    theme: "stripe",
    variables: {
      colorPrimary: "#6366f1",
    },
  };

  const options = {
    clientSecret,
    appearance,
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Checkout</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Checkout Form */}
        <div>
          {!clientSecret ? (
            <ShippingForm onSubmit={handleShippingSubmit} />
          ) : (
            <Elements options={options} stripe={stripePromise}>
              <CheckoutForm orderId={orderId} totals={totals} />
            </Elements>
          )}
        </div>

        {/* Right: Order Summary */}
        <div>
          <div className="bg-gray-50 rounded-lg p-6 sticky top-4">
            <h2 className="text-xl font-semibold mb-4">Order Summary</h2>

            {/* Cart Items */}
            <div className="space-y-4 mb-6">
              {cart.items.map((item) => (
                <div key={item.id} className="flex gap-4">
                  <img
                    src={item.image}
                    alt={item.product_name}
                    className="w-16 h-16 rounded object-cover"
                  />
                  <div className="flex-1">
                    <p className="font-medium">{item.product_name}</p>
                    {item.variant_name && (
                      <p className="text-sm text-gray-600">
                        {item.variant_name}
                      </p>
                    )}
                    <p className="text-sm text-gray-600">
                      Qty: {item.quantity}
                    </p>
                  </div>
                  <p className="font-semibold">
                    ${(item.price * item.quantity).toFixed(2)}
                  </p>
                </div>
              ))}
            </div>

            {/* Totals */}
            <div className="border-t pt-4 space-y-2">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>${(totals?.subtotal || cart.subtotal).toFixed(2)}</span>
              </div>
              {totals && (
                <>
                  <div className="flex justify-between">
                    <span>Shipping</span>
                    <span>${totals.shipping.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tax</span>
                    <span>${totals.tax.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-lg font-bold border-t pt-2">
                    <span>Total</span>
                    <span>${totals.total.toFixed(2)}</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Shipping Form Component
function ShippingForm({ onSubmit }) {
  const [formData, setFormData] = useState({
    email: "",
    first_name: "",
    last_name: "",
    address1: "",
    address2: "",
    city: "",
    state: "",
    zip_code: "",
    phone: "",
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      email: formData.email,
      shipping_address: {
        first_name: formData.first_name,
        last_name: formData.last_name,
        address1: formData.address1,
        address2: formData.address2,
        city: formData.city,
        state: formData.state,
        zip_code: formData.zip_code,
        phone: formData.phone,
        country: "United States",
      },
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-xl font-semibold mb-4">Shipping Information</h2>

      <input
        type="email"
        placeholder="Email"
        required
        value={formData.email}
        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
      />

      <div className="grid grid-cols-2 gap-4">
        <input
          type="text"
          placeholder="First Name"
          required
          value={formData.first_name}
          onChange={(e) =>
            setFormData({ ...formData, first_name: e.target.value })
          }
          className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
        />
        <input
          type="text"
          placeholder="Last Name"
          required
          value={formData.last_name}
          onChange={(e) =>
            setFormData({ ...formData, last_name: e.target.value })
          }
          className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
        />
      </div>

      <input
        type="text"
        placeholder="Address Line 1"
        required
        value={formData.address1}
        onChange={(e) => setFormData({ ...formData, address1: e.target.value })}
        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
      />

      <input
        type="text"
        placeholder="Address Line 2 (Optional)"
        value={formData.address2}
        onChange={(e) => setFormData({ ...formData, address2: e.target.value })}
        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
      />

      <div className="grid grid-cols-3 gap-4">
        <input
          type="text"
          placeholder="City"
          required
          value={formData.city}
          onChange={(e) => setFormData({ ...formData, city: e.target.value })}
          className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
        />
        <input
          type="text"
          placeholder="State"
          required
          value={formData.state}
          onChange={(e) => setFormData({ ...formData, state: e.target.value })}
          className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
        />
        <input
          type="text"
          placeholder="ZIP"
          required
          value={formData.zip_code}
          onChange={(e) =>
            setFormData({ ...formData, zip_code: e.target.value })
          }
          className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
        />
      </div>

      <input
        type="tel"
        placeholder="Phone"
        required
        value={formData.phone}
        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
      />

      <button
        type="submit"
        className="w-full bg-purple-600 text-white py-3 rounded-lg font-semibold hover:bg-purple-700 transition"
      >
        Continue to Payment
      </button>
    </form>
  );
}
```

---

## 🚀 Phase 5: Order Fulfillment Integration (Week 9-10)

### **Goals**

- [ ] Auto-generate gangsheets for physical product orders
- [ ] Auto-generate download links for digital products
- [ ] Send order confirmation emails
- [ ] Update inventory levels
- [ ] Integration with existing NAS storage

### **Step 5.1: Order Fulfillment Service**

`server/src/services/ecommerce_fulfillment.py`:

```python
from sqlalchemy.orm import Session
from server.src.entities.ecommerce.order import Order, OrderItem
from server.src.entities.ecommerce.product import Product, ProductType
from server.src.utils.gangsheet_engine import create_gang_sheets_from_db
from server.src.utils.nas_storage import nas_storage
from server.src.services.email_service import send_order_confirmation_email
import logging
import os
from typing import List

class OrderFulfillmentService:
    """Service for fulfilling ecommerce orders."""

    def __init__(self, db: Session):
        self.db = db

    async def fulfill_order(self, order_id: str):
        """
        Fulfill an order by:
        1. Processing physical products (generate gangsheets)
        2. Processing digital products (generate download links)
        3. Updating inventory
        4. Sending confirmation email
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        logging.info(f"Starting fulfillment for order {order.order_number}")

        try:
            # Separate items by type
            physical_items = []
            digital_items = []

            for item in order.items:
                product = self.db.query(Product).filter(Product.id == item.product_id).first()
                if product.product_type == ProductType.PHYSICAL:
                    physical_items.append(item)
                else:
                    digital_items.append(item)

            # Process physical products
            if physical_items:
                await self._fulfill_physical_products(order, physical_items)

            # Process digital products
            if digital_items:
                await self._fulfill_digital_products(order, digital_items)

            # Update inventory
            await self._update_inventory(order.items)

            # Update order status
            order.fulfillment_status = 'fulfilled'
            self.db.commit()

            # Send confirmation email
            await send_order_confirmation_email(order)

            logging.info(f"✅ Order {order.order_number} fulfilled successfully")

        except Exception as e:
            logging.error(f"Error fulfilling order {order.order_number}: {e}")
            order.internal_note = f"Fulfillment error: {str(e)}"
            self.db.commit()
            raise

    async def _fulfill_physical_products(self, order: Order, items: List[OrderItem]):
        """Generate gangsheets for physical products."""
        logging.info(f"Generating gangsheets for {len(items)} physical items")

        # Group items by template
        items_by_template = {}
        for item in items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            template_name = product.template_name or 'UVDTF 16oz'

            if template_name not in items_by_template:
                items_by_template[template_name] = []

            # Add item quantity times
            for _ in range(item.quantity):
                items_by_template[template_name].append({
                    'design_id': product.design_id,
                    'product_name': item.product_name,
                })

        # Generate gangsheet for each template
        for template_name, template_items in items_by_template.items():
            try:
                # Use existing gangsheet engine
                result = create_gang_sheets_from_db(
                    db=self.db,
                    user_id=None,  # System-generated
                    template_name=template_name,
                    output_path=f"/tmp/gangsheets/{order.order_number}",
                    design_ids=[item['design_id'] for item in template_items]
                )

                if result:
                    # Upload to NAS
                    gangsheet_file = result.get('file_path')
                    nas_path = f"Orders/{order.order_number}/gangsheet_{template_name}.png"

                    nas_storage.upload_file(
                        local_file_path=gangsheet_file,
                        shop_name="Ecommerce",  # Your shop name
                        relative_path=nas_path
                    )

                    # Update order items
                    for item in items:
                        item.gangsheet_generated = True
                        item.gangsheet_file_path = nas_path

                    logging.info(f"✅ Gangsheet generated: {nas_path}")

            except Exception as e:
                logging.error(f"Error generating gangsheet for {template_name}: {e}")

        self.db.commit()

    async def _fulfill_digital_products(self, order: Order, items: List[OrderItem]):
        """Generate download links for digital products."""
        logging.info(f"Generating download links for {len(items)} digital items")

        from datetime import datetime, timedelta
        import secrets

        for item in items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()

            # Generate secure download token
            token = secrets.token_urlsafe(32)
            download_url = f"{os.getenv('FRONTEND_URL')}/downloads/{token}"

            # Store download URL and expiration (7 days)
            item.download_url = download_url
            item.download_expires_at = datetime.utcnow() + timedelta(days=7)
            item.is_fulfilled = True

            # TODO: Store token in separate table for validation
            # DownloadToken(token=token, product_id=..., order_item_id=...)

        self.db.commit()

    async def _update_inventory(self, items: List[OrderItem]):
        """Update product inventory levels."""
        for item in items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()

            if product.track_inventory:
                if product.inventory_quantity >= item.quantity:
                    product.inventory_quantity -= item.quantity
                else:
                    logging.warning(
                        f"Insufficient inventory for {product.name}. "
                        f"Available: {product.inventory_quantity}, Ordered: {item.quantity}"
                    )

        self.db.commit()


# Background job integration
async def process_order_fulfillment(order_id: str, db: Session):
    """Background task to fulfill order."""
    service = OrderFulfillmentService(db)
    await service.fulfill_order(order_id)
```

### **Step 5.2: Email Service**

`server/src/services/email_service.py`:

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
import logging

async def send_order_confirmation_email(order):
    """Send order confirmation email to customer."""
    try:
        # Build email content
        items_html = ""
        for item in order.items:
            items_html += f"""
            <tr>
                <td>{item.product_name} {f'- {item.variant_name}' if item.variant_name else ''}</td>
                <td>{item.quantity}</td>
                <td>${item.price:.2f}</td>
                <td>${item.total:.2f}</td>
            </tr>
            """

        email_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Order Confirmation - {order.order_number}</h2>
            <p>Hi {order.shipping_address.get('first_name')},</p>
            <p>Thank you for your order! We've received your payment and are processing your order.</p>

            <h3>Order Details</h3>
            <table border="1" cellpadding="10" style="border-collapse: collapse;">
                <tr>
                    <th>Product</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>Total</th>
                </tr>
                {items_html}
            </table>

            <h3>Order Summary</h3>
            <p>Subtotal: ${order.subtotal:.2f}</p>
            <p>Shipping: ${order.shipping:.2f}</p>
            <p>Tax: ${order.tax:.2f}</p>
            <p><strong>Total: ${order.total:.2f}</strong></p>

            <h3>Shipping Address</h3>
            <p>
                {order.shipping_address.get('first_name')} {order.shipping_address.get('last_name')}<br>
                {order.shipping_address.get('address1')}<br>
                {f"{order.shipping_address.get('address2')}<br>" if order.shipping_address.get('address2') else ''}
                {order.shipping_address.get('city')}, {order.shipping_address.get('state')} {order.shipping_address.get('zip_code')}
            </p>

            <p>You can track your order status in your <a href="{os.getenv('FRONTEND_URL')}/account/orders">account dashboard</a>.</p>

            <p>Thanks,<br>Your Shop Name Team</p>
        </body>
        </html>
        """

        # Send email via SendGrid
        message = Mail(
            from_email='orders@yourshop.com',
            to_emails=order.guest_email,
            subject=f'Order Confirmation - {order.order_number}',
            html_content=email_content
        )

        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)

        logging.info(f"Confirmation email sent for order {order.order_number}")
        return True

    except Exception as e:
        logging.error(f"Failed to send confirmation email: {e}")
        return False
```

---

## 🧪 Phase 6: Testing & Launch (Week 11-12)

### **Testing Checklist**

**Backend API Testing:**

```bash
# Test products endpoint
curl https://your-domain.com/api/storefront/products

# Test cart
curl -X POST https://your-domain.com/api/storefront/cart/add \
  -H "Content-Type: application/json" \
  -d '{"product_id": "...", "quantity": 1}'

# Test Stripe webhook
stripe listen --forward-to localhost:3003/api/webhooks/stripe
```

**Frontend Testing:**

- [ ] Browse products catalog
- [ ] Search functionality
- [ ] Add to cart
- [ ] Update cart quantities
- [ ] Remove from cart
- [ ] Checkout flow (use Stripe test cards)
- [ ] Order confirmation page
- [ ] Customer account registration
- [ ] Customer account login
- [ ] Order history view
- [ ] Digital product downloads

**Stripe Test Cards:**

```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
3D Secure: 4000 0025 0000 3155
```

### **Deployment**

**Deploy Backend:**

```bash
# Update Railway environment variables
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
SENDGRID_API_KEY=SG...
FRONTEND_URL=https://shop.yourstore.com

# Deploy
git push production main
```

**Deploy Storefront:**

```bash
cd storefront
npm run build

# Deploy to Vercel/Netlify
vercel --prod
# or
netlify deploy --prod
```

### **Launch Checklist**

- [ ] SSL certificate configured
- [ ] Custom domain setup
- [ ] Stripe account in live mode
- [ ] Email service configured
- [ ] Google Analytics added
- [ ] Facebook Pixel added
- [ ] Privacy policy page
- [ ] Terms of service page
- [ ] Refund policy page
- [ ] Contact page
- [ ] Favicon and social share images
- [ ] Test complete purchase flow
- [ ] Test email notifications
- [ ] Test gangsheet generation
- [ ] Test digital downloads

---

## 📈 Post-Launch: Advanced Features

### **Week 13+: Enhancements**

1. **Marketing Features:**
   - Discount codes
   - Buy X Get Y promotions
   - Flash sales
   - Abandoned cart recovery emails

2. **Customer Experience:**
   - Product reviews & ratings
   - Wishlist
   - Product recommendations
   - Size guides

3. **Analytics:**
   - Sales dashboard
   - Top products report
   - Customer lifetime value
   - Conversion tracking

4. **Operations:**
   - Inventory alerts
   - Low stock notifications
   - Automated reordering
   - Supplier integration

5. **SEO & Marketing:**
   - Blog for content marketing
   - Email newsletter
   - Social media integration
   - Google Shopping feed

---

## 💰 Cost Estimate

**Monthly Costs:**

- Railway hosting: $20-50/month
- Vercel/Netlify (storefront): $0-20/month
- PostgreSQL database: Included in Railway
- Stripe fees: 2.9% + $0.30 per transaction
- SendGrid (email): $0-15/month (up to 40,000 emails)
- Domain name: $12/year
- SSL certificate: Free (Let's Encrypt)

**Total: ~$30-100/month** (depending on traffic)

---

## 📞 Support & Resources

**Documentation:**

- Stripe Docs: https://stripe.com/docs
- React Router: https://reactrouter.com
- Zustand: https://github.com/pmndrs/zustand
- FastAPI: https://fastapi.tiangolo.com
- Tailwind CSS: https://tailwindcss.com

**Need Help?**

- Review each phase step-by-step
- Test components individually before integration
- Use Stripe test mode during development
- Monitor Railway logs for errors

---

**📄 Continue to:** [ECOMMERCE_PLATFORM_GUIDE_PART4.md](./ECOMMERCE_PLATFORM_GUIDE_PART4.md) for complete Phase 3 components (ProductDetail, Header, API services), explicit Phase 4 (Payment & Checkout), and final implementation checklist.

---

**Created:** 2025-12-05
**Last Updated:** 2025-12-05
**Version:** 1.0
