import os
import time
import hmac
import hashlib
import base64
import logging
from typing import Optional, Dict, List, Any, BinaryIO
from datetime import datetime, timezone
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sqlalchemy.orm import Session
from server.src.entities.shopify_store import ShopifyStore

logger = logging.getLogger(__name__)

class ShopifyAPIError(Exception):
    """Base exception for Shopify API errors"""
    pass

class ShopifyRateLimitError(ShopifyAPIError):
    """Raised when rate limit is exceeded"""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")

class ShopifyAuthError(ShopifyAPIError):
    """Raised when authentication fails"""
    pass

class ShopifyNotFoundError(ShopifyAPIError):
    """Raised when resource is not found"""
    pass

class ShopifyClient:
    """
    Reusable Shopify API client with rate limiting, retry logic, and comprehensive error handling.

    Supports both REST API operations for orders, products, and images.
    Includes webhook signature verification for secure webhook handling.
    """

    API_VERSION = "2023-10"
    BASE_RETRY_DELAY = 0.5  # Base delay for exponential backoff
    MAX_RETRY_DELAY = 60    # Maximum delay between retries
    MAX_RETRIES = 5         # Maximum number of retries

    def __init__(self, db: Session):
        """
        Initialize Shopify client with database session for token retrieval.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.session = requests.Session()

        # Configure retry strategy for connection issues
        retry_strategy = Retry(
            total=3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get_store_info(self, store_id: str) -> ShopifyStore:
        """
        Retrieve store information from database.

        Args:
            store_id: UUID of the store

        Returns:
            ShopifyStore object

        Raises:
            ShopifyNotFoundError: If store not found or inactive
        """
        store = self.db.query(ShopifyStore).filter(
            ShopifyStore.id == store_id,
            ShopifyStore.is_active == True
        ).first()

        if not store:
            raise ShopifyNotFoundError(f"Active store with ID {store_id} not found")

        return store

    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """
        Get standard headers for Shopify API requests.

        Args:
            access_token: Shopify access token

        Returns:
            Dictionary of headers
        """
        return {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'EtsySellerAutomater/1.0'
        }

    def _make_request_with_retry(self, method: str, url: str, headers: Dict[str, str],
                                **kwargs) -> requests.Response:
        """
        Make HTTP request with exponential backoff retry for rate limits.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Full URL for the request
            headers: Request headers
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            ShopifyRateLimitError: If rate limit exceeded after max retries
            ShopifyAuthError: If authentication fails
            ShopifyAPIError: For other API errors
        """
        retry_count = 0
        delay = self.BASE_RETRY_DELAY

        while retry_count <= self.MAX_RETRIES:
            try:
                response = self.session.request(method, url, headers=headers, timeout=30, **kwargs)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', delay))

                    if retry_count >= self.MAX_RETRIES:
                        raise ShopifyRateLimitError(retry_after)

                    logger.warning(f"Rate limit hit, retrying after {retry_after} seconds (attempt {retry_count + 1})")
                    time.sleep(retry_after)
                    retry_count += 1
                    delay = min(delay * 2, self.MAX_RETRY_DELAY)
                    continue

                # Handle authentication errors
                if response.status_code == 401:
                    raise ShopifyAuthError("Invalid or expired access token")

                # Handle not found
                if response.status_code == 404:
                    raise ShopifyNotFoundError("Resource not found")

                # Handle other client/server errors
                if response.status_code >= 400:
                    error_msg = f"Shopify API error {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise ShopifyAPIError(error_msg)

                # Success
                return response

            except requests.exceptions.RequestException as e:
                if retry_count >= self.MAX_RETRIES:
                    raise ShopifyAPIError(f"Request failed after {self.MAX_RETRIES} retries: {e}")

                logger.warning(f"Request failed, retrying (attempt {retry_count + 1}): {e}")
                time.sleep(delay)
                retry_count += 1
                delay = min(delay * 2, self.MAX_RETRY_DELAY)

        raise ShopifyAPIError("Maximum retries exceeded")

    def get_orders(self, store_id: str, since_time: Optional[datetime] = None,
                   limit: int = 250, status: str = "any") -> List[Dict[str, Any]]:
        """
        Fetch orders from Shopify store.

        Args:
            store_id: UUID of the store
            since_time: Optional datetime to fetch orders since (UTC)
            limit: Maximum number of orders to fetch (1-250)
            status: Order status filter (any, open, closed, cancelled)

        Returns:
            List of order dictionaries

        Raises:
            ShopifyAPIError: If API request fails
        """
        store = self._get_store_info(store_id)
        url = f"https://{store.shop_domain}/admin/api/{self.API_VERSION}/orders.json"

        params = {
            'limit': min(limit, 250),
            'status': status
        }

        if since_time:
            # Convert to ISO format that Shopify expects
            params['created_at_min'] = since_time.isoformat()

        headers = self._get_headers(store.access_token)

        try:
            logger.info(f"🔗 Fetching orders from {store.shop_name}")
            logger.info(f"   URL: {url}")
            logger.info(f"   Params: {params}")

            response = self._make_request_with_retry('GET', url, headers, params=params)
            data = response.json()

            logger.info(f"✅ Successfully fetched {len(data.get('orders', []))} orders from store {store.shop_name}")
            return data.get('orders', [])

        except ShopifyAPIError as e:
            logger.error(f"❌ Shopify API error fetching orders from {store.shop_name}: {e}")
            # If it's a 400 error about ID, it might be an empty store - return empty list
            if "expected String to be a id" in str(e):
                logger.warning(f"⚠️  Store {store.shop_name} may be new/empty - returning empty orders list")
                return []
            raise
        except Exception as e:
            logger.error(f"❌ Failed to fetch orders from store {store_id}: {e}")
            raise

    def get_products(self, store_id: str, limit: int = 250,
                    published_status: str = "published") -> List[Dict[str, Any]]:
        """
        Fetch products from Shopify store.

        Args:
            store_id: UUID of the store
            limit: Maximum number of products to fetch (1-250)
            published_status: Filter by published status (published, unpublished, any)

        Returns:
            List of product dictionaries

        Raises:
            ShopifyAPIError: If API request fails
        """
        store = self._get_store_info(store_id)
        url = f"https://{store.shop_domain}/admin/api/{self.API_VERSION}/products.json"

        params = {
            'limit': min(limit, 250),
            'published_status': published_status
        }

        headers = self._get_headers(store.access_token)

        try:
            response = self._make_request_with_retry('GET', url, headers, params=params)
            data = response.json()

            logger.info(f"Successfully fetched {len(data.get('products', []))} products from store {store.shop_name}")
            return data.get('products', [])

        except Exception as e:
            logger.error(f"Failed to fetch products from store {store_id}: {e}")
            raise

    def create_product(self, store_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product in Shopify store.

        Args:
            store_id: UUID of the store
            product_data: Product data dictionary following Shopify product schema

        Example product_data:
        {
            "title": "Product Title",
            "body_html": "<p>Product description</p>",
            "vendor": "Vendor Name",
            "product_type": "Type",
            "tags": "tag1,tag2",
            "variants": [
                {
                    "price": "10.00",
                    "sku": "SKU123",
                    "inventory_quantity": 100
                }
            ]
        }

        Returns:
            Created product dictionary

        Raises:
            ShopifyAPIError: If API request fails
        """
        store = self._get_store_info(store_id)
        url = f"https://{store.shop_domain}/admin/api/{self.API_VERSION}/products.json"

        headers = self._get_headers(store.access_token)
        payload = {"product": product_data}

        try:
            response = self._make_request_with_retry('POST', url, headers, json=payload)
            data = response.json()

            product = data.get('product', {})
            logger.info(f"Successfully created product '{product.get('title')}' with ID {product.get('id')} in store {store.shop_name}")
            return product

        except Exception as e:
            logger.error(f"Failed to create product in store {store_id}: {e}")
            raise

    def upload_product_image(self, store_id: str, product_id: str,
                           image_file: BinaryIO, filename: str,
                           alt_text: Optional[str] = None,
                           position: Optional[int] = None) -> Dict[str, Any]:
        """
        Upload an image to an existing product.

        Args:
            store_id: UUID of the store
            product_id: Shopify product ID
            image_file: Binary file object of the image
            filename: Name of the image file
            alt_text: Optional alt text for the image
            position: Optional position of the image (1 is first)

        Returns:
            Created image dictionary

        Raises:
            ShopifyAPIError: If API request fails
        """
        store = self._get_store_info(store_id)
        url = f"https://{store.shop_domain}/admin/api/{self.API_VERSION}/products/{product_id}/images.json"

        # Read file content and encode as base64
        image_content = image_file.read()
        encoded_image = base64.b64encode(image_content).decode('utf-8')

        image_data = {
            "filename": filename,
            "attachment": encoded_image
        }

        if alt_text:
            image_data["alt"] = alt_text

        if position:
            image_data["position"] = position

        headers = self._get_headers(store.access_token)
        payload = {"image": image_data}

        try:
            response = self._make_request_with_retry('POST', url, headers, json=payload)
            data = response.json()

            image = data.get('image', {})
            logger.info(f"Successfully uploaded image {filename} to product {product_id} in store {store.shop_name}")
            return image

        except Exception as e:
            logger.error(f"Failed to upload image to product {product_id} in store {store_id}: {e}")
            raise

    def update_product(self, store_id: str, product_id: str,
                      product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing product in Shopify store.

        Args:
            store_id: UUID of the store
            product_id: Shopify product ID to update
            product_data: Updated product data dictionary

        Returns:
            Updated product dictionary

        Raises:
            ShopifyAPIError: If API request fails
        """
        store = self._get_store_info(store_id)
        url = f"https://{store.shop_domain}/admin/api/{self.API_VERSION}/products/{product_id}.json"

        headers = self._get_headers(store.access_token)
        payload = {"product": product_data}

        try:
            response = self._make_request_with_retry('PUT', url, headers, json=payload)
            data = response.json()

            product = data.get('product', {})
            logger.info(f"Successfully updated product {product_id} in store {store.shop_name}")
            return product

        except Exception as e:
            logger.error(f"Failed to update product {product_id} in store {store_id}: {e}")
            raise

    def delete_product(self, store_id: str, product_id: str) -> bool:
        """
        Delete a product from Shopify store.

        Args:
            store_id: UUID of the store
            product_id: Shopify product ID to delete

        Returns:
            True if deletion was successful

        Raises:
            ShopifyAPIError: If API request fails
        """
        store = self._get_store_info(store_id)
        url = f"https://{store.shop_domain}/admin/api/{self.API_VERSION}/products/{product_id}.json"

        headers = self._get_headers(store.access_token)

        try:
            response = self._make_request_with_retry('DELETE', url, headers)

            logger.info(f"Successfully deleted product {product_id} from store {store.shop_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete product {product_id} from store {store_id}: {e}")
            raise

    @staticmethod
    def verify_webhook_signature(headers: Dict[str, str], body: bytes,
                                webhook_secret: Optional[str] = None) -> bool:
        """
        Verify the signature of a Shopify webhook to ensure authenticity.

        Args:
            headers: Request headers dictionary
            body: Raw request body as bytes
            webhook_secret: Webhook secret from Shopify (defaults to env var)

        Returns:
            True if signature is valid, False otherwise

        Raises:
            ShopifyAPIError: If webhook secret is not configured
        """
        if not webhook_secret:
            webhook_secret = os.getenv('SHOPIFY_WEBHOOK_SECRET')

        if not webhook_secret:
            raise ShopifyAPIError("SHOPIFY_WEBHOOK_SECRET not configured")

        # Get the signature from headers
        signature_header = headers.get('X-Shopify-Hmac-Sha256')
        if not signature_header:
            logger.warning("No webhook signature found in headers")
            return False

        # Calculate expected signature
        expected_signature = base64.b64encode(
            hmac.new(
                webhook_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')

        # Compare signatures using constant-time comparison
        is_valid = hmac.compare_digest(expected_signature, signature_header)

        if not is_valid:
            logger.warning("Webhook signature verification failed")
        else:
            logger.info("Webhook signature verified successfully")

        return is_valid

    def get_product_by_id(self, store_id: str, product_id: str) -> Dict[str, Any]:
        """
        Get a specific product by ID.

        Args:
            store_id: UUID of the store
            product_id: Shopify product ID

        Returns:
            Product dictionary

        Raises:
            ShopifyAPIError: If API request fails
        """
        store = self._get_store_info(store_id)
        url = f"https://{store.shop_domain}/admin/api/{self.API_VERSION}/products/{product_id}.json"

        headers = self._get_headers(store.access_token)

        try:
            response = self._make_request_with_retry('GET', url, headers)
            data = response.json()

            product = data.get('product', {})
            logger.info(f"Successfully fetched product {product_id} from store {store.shop_name}")
            return product

        except Exception as e:
            logger.error(f"Failed to fetch product {product_id} from store {store_id}: {e}")
            raise

    def get_order_by_id(self, store_id: str, order_id: str) -> Dict[str, Any]:
        """
        Get a specific order by ID.

        Args:
            store_id: UUID of the store
            order_id: Shopify order ID

        Returns:
            Order dictionary

        Raises:
            ShopifyAPIError: If API request fails
        """
        store = self._get_store_info(store_id)
        url = f"https://{store.shop_domain}/admin/api/{self.API_VERSION}/orders/{order_id}.json"

        headers = self._get_headers(store.access_token)

        try:
            response = self._make_request_with_retry('GET', url, headers)
            data = response.json()

            order = data.get('order', {})
            logger.info(f"Successfully fetched order {order_id} from store {store.shop_name}")
            return order

        except Exception as e:
            logger.error(f"Failed to fetch order {order_id} from store {store_id}: {e}")
            raise

    def test_connection(self, store_id: str) -> Dict[str, Any]:
        """
        Test the connection to a Shopify store by fetching shop information.

        Args:
            store_id: UUID of the store

        Returns:
            Shop information dictionary

        Raises:
            ShopifyAPIError: If connection test fails
        """
        store = self._get_store_info(store_id)
        url = f"https://{store.shop_domain}/admin/api/{self.API_VERSION}/shop.json"

        headers = self._get_headers(store.access_token)

        try:
            response = self._make_request_with_retry('GET', url, headers)
            data = response.json()

            shop = data.get('shop', {})
            logger.info(f"Successfully connected to Shopify store: {shop.get('name', 'Unknown')}")
            return shop

        except Exception as e:
            logger.error(f"Failed to test connection to store {store_id}: {e}")
            raise