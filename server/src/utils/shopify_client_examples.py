"""
Example usage of the Shopify API client.

This file demonstrates how to use the ShopifyClient and ShopifyService
for common Shopify operations.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from server.src.utils.shopify_client import ShopifyClient
from server.src.routes.shopify.service import ShopifyService

def example_usage():
    """
    Example usage patterns for the Shopify API client.
    """

    # Initialize with database session
    # db = get_db_session()  # Your database session
    # service = ShopifyService(db)
    # user_id = "your-user-uuid"

    print("Shopify API Client Usage Examples")
    print("=" * 40)

    # 1. Fetch recent orders
    print("\n1. Fetching Recent Orders:")
    print("""
    since_time = datetime(2023, 1, 1, tzinfo=timezone.utc)
    orders = service.get_orders(user_id, since_time=since_time, limit=50)

    for order in orders:
        print(f"Order #{order['name']}: ${order['total_price']}")
    """)

    # 2. Fetch products
    print("\n2. Fetching Products:")
    print("""
    products = service.get_products(user_id, limit=100)

    for product in products:
        print(f"Product: {product['title']} - Handle: {product['handle']}")
    """)

    # 3. Create a new product
    print("\n3. Creating a Product:")
    print("""
    product_data = {
        "title": "Amazing T-Shirt",
        "body_html": "<p>This is an amazing t-shirt!</p>",
        "vendor": "My Store",
        "product_type": "Apparel",
        "tags": "shirt,cotton,comfortable",
        "variants": [
            {
                "option1": "Small",
                "price": "19.99",
                "sku": "TSHIRT-S",
                "inventory_quantity": 50,
                "weight": 200,
                "weight_unit": "g"
            },
            {
                "option1": "Medium",
                "price": "19.99",
                "sku": "TSHIRT-M",
                "inventory_quantity": 50,
                "weight": 200,
                "weight_unit": "g"
            }
        ],
        "options": [
            {
                "name": "Size",
                "values": ["Small", "Medium", "Large"]
            }
        ]
    }

    created_product = service.create_product(user_id, product_data)
    print(f"Created product with ID: {created_product['id']}")
    """)

    # 4. Upload product image
    print("\n4. Uploading Product Image:")
    print("""
    # Using FastAPI UploadFile
    @router.post("/upload-image")
    async def upload_image(
        product_id: str,
        image: UploadFile = File(...),
        current_user: CurrentUser,
        db: Session = Depends(get_db)
    ):
        service = ShopifyService(db)

        uploaded_image = service.upload_product_image(
            user_id=current_user.get_uuid(),
            product_id=product_id,
            image_file=image,
            alt_text="Product image",
            position=1
        )

        return {"image_url": uploaded_image["src"]}
    """)

    # 5. Webhook verification
    print("\n5. Verifying Webhooks:")
    print("""
    @router.post("/webhook/order-created")
    async def handle_order_webhook(request: Request):
        headers = dict(request.headers)
        body = await request.body()

        # Verify webhook signature
        is_valid = ShopifyClient.verify_webhook_signature(headers, body)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

        # Process the webhook data
        webhook_data = json.loads(body)
        order_id = webhook_data.get("id")

        # Handle the new order...

        return {"status": "processed"}
    """)

    # 6. Error handling
    print("\n6. Error Handling:")
    print("""
    try:
        products = service.get_products(user_id)
    except HTTPException as e:
        if e.status_code == 401:
            # Token expired or invalid
            print("Please reconnect your Shopify store")
        elif e.status_code == 429:
            # Rate limit exceeded
            print("Too many requests, please try again later")
        elif e.status_code == 404:
            # Store not found
            print("No Shopify store connected")
        else:
            print(f"API error: {e.detail}")
    """)

    # 7. Testing connection
    print("\n7. Testing Store Connection:")
    print("""
    try:
        shop_info = service.test_connection(user_id)
        print(f"Connected to: {shop_info['name']}")
        print(f"Domain: {shop_info['domain']}")
        print(f"Email: {shop_info['email']}")
    except HTTPException as e:
        print(f"Connection failed: {e.detail}")
    """)

def rate_limiting_example():
    """
    Example of how rate limiting works automatically.
    """
    print("\nRate Limiting Example:")
    print("=" * 30)
    print("""
    The ShopifyClient automatically handles rate limiting:

    1. When a 429 (Too Many Requests) response is received
    2. The client waits for the time specified in the 'Retry-After' header
    3. It retries the request with exponential backoff
    4. Maximum of 5 retries before raising ShopifyRateLimitError

    Example configuration:
    - Base retry delay: 0.5 seconds
    - Maximum retry delay: 60 seconds
    - Maximum retries: 5

    This ensures your application doesn't get blocked by Shopify's API limits.
    """)

def webhook_setup_example():
    """
    Example of setting up webhooks in Shopify.
    """
    print("\nWebhook Setup Guide:")
    print("=" * 25)
    print("""
    1. In your Shopify Admin:
       - Go to Settings > Notifications
       - Scroll down to "Webhooks" section
       - Click "Create webhook"

    2. Configure webhook:
       - Event: Choose event (e.g., "Order created")
       - Format: JSON
       - URL: https://yourapp.com/api/shopify/webhooks/order-created

    3. Set webhook secret in environment:
       SHOPIFY_WEBHOOK_SECRET=your_webhook_secret

    4. Verify webhook in your endpoint:
       is_valid = ShopifyClient.verify_webhook_signature(headers, body)

    Common webhook events:
    - orders/create: New order placed
    - orders/updated: Order modified
    - orders/paid: Payment received
    - products/create: New product added
    - products/update: Product modified
    """)

if __name__ == "__main__":
    example_usage()
    rate_limiting_example()
    webhook_setup_example()