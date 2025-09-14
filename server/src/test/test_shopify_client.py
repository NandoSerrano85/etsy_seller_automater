import pytest
import hmac
import hashlib
import base64
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import requests
from sqlalchemy.orm import Session
from server.src.utils.shopify_client import (
    ShopifyClient,
    ShopifyAPIError,
    ShopifyAuthError,
    ShopifyNotFoundError,
    ShopifyRateLimitError
)
from server.src.entities.shopify_store import ShopifyStore

class TestShopifyClient:
    """Test suite for ShopifyClient"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_store(self):
        """Mock ShopifyStore"""
        store = Mock(spec=ShopifyStore)
        store.id = "test-store-id"
        store.shop_domain = "test-store.myshopify.com"
        store.shop_name = "Test Store"
        store.access_token = "test-access-token"
        store.is_active = True
        return store

    @pytest.fixture
    def client(self, mock_db):
        """ShopifyClient instance"""
        return ShopifyClient(mock_db)

    def test_get_store_info_success(self, client, mock_db, mock_store):
        """Test successful store info retrieval"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        result = client._get_store_info("test-store-id")

        assert result == mock_store
        mock_db.query.assert_called_once()

    def test_get_store_info_not_found(self, client, mock_db):
        """Test store not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ShopifyNotFoundError):
            client._get_store_info("nonexistent-store-id")

    @patch('server.src.utils.shopify_client.requests.Session.request')
    def test_get_orders_success(self, mock_request, client, mock_db, mock_store):
        """Test successful orders fetching"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "orders": [
                {"id": 1, "name": "#1001", "total_price": "100.00"},
                {"id": 2, "name": "#1002", "total_price": "200.00"}
            ]
        }
        mock_request.return_value = mock_response

        orders = client.get_orders("test-store-id")

        assert len(orders) == 2
        assert orders[0]["id"] == 1
        assert orders[1]["name"] == "#1002"

    @patch('server.src.utils.shopify_client.requests.Session.request')
    def test_get_products_success(self, mock_request, client, mock_db, mock_store):
        """Test successful products fetching"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "products": [
                {"id": 1, "title": "Product 1", "price": "50.00"},
                {"id": 2, "title": "Product 2", "price": "75.00"}
            ]
        }
        mock_request.return_value = mock_response

        products = client.get_products("test-store-id")

        assert len(products) == 2
        assert products[0]["title"] == "Product 1"
        assert products[1]["id"] == 2

    @patch('server.src.utils.shopify_client.requests.Session.request')
    def test_create_product_success(self, mock_request, client, mock_db, mock_store):
        """Test successful product creation"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        product_data = {
            "title": "New Product",
            "body_html": "<p>Description</p>",
            "vendor": "Test Vendor",
            "product_type": "Widget",
            "variants": [{"price": "25.00", "sku": "SKU123"}]
        }

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "product": {
                "id": 123,
                "title": "New Product",
                "handle": "new-product"
            }
        }
        mock_request.return_value = mock_response

        result = client.create_product("test-store-id", product_data)

        assert result["id"] == 123
        assert result["title"] == "New Product"

    @patch('server.src.utils.shopify_client.requests.Session.request')
    def test_upload_product_image_success(self, mock_request, client, mock_db, mock_store):
        """Test successful image upload"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        mock_file = Mock()
        mock_file.read.return_value = b"fake image data"

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "image": {
                "id": 456,
                "src": "https://cdn.shopify.com/image.jpg",
                "alt": "Test image"
            }
        }
        mock_request.return_value = mock_response

        result = client.upload_product_image(
            "test-store-id", "123", mock_file, "test.jpg", "Test image"
        )

        assert result["id"] == 456
        assert result["alt"] == "Test image"

    @patch('server.src.utils.shopify_client.requests.Session.request')
    def test_rate_limit_handling(self, mock_request, client, mock_db, mock_store):
        """Test rate limit handling with retry"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        # First call returns 429, second call succeeds
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"orders": []}

        mock_request.side_effect = [rate_limit_response, success_response]

        with patch('time.sleep') as mock_sleep:
            orders = client.get_orders("test-store-id")

        assert orders == []
        mock_sleep.assert_called_once_with(1)
        assert mock_request.call_count == 2

    @patch('server.src.utils.shopify_client.requests.Session.request')
    def test_auth_error_handling(self, mock_request, client, mock_db, mock_store):
        """Test authentication error handling"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response

        with pytest.raises(ShopifyAuthError):
            client.get_orders("test-store-id")

    @patch('server.src.utils.shopify_client.requests.Session.request')
    def test_not_found_error_handling(self, mock_request, client, mock_db, mock_store):
        """Test not found error handling"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        with pytest.raises(ShopifyNotFoundError):
            client.get_product_by_id("test-store-id", "nonexistent")

    def test_verify_webhook_signature_valid(self):
        """Test valid webhook signature verification"""
        webhook_secret = "test-secret"
        body = b'{"test": "data"}'

        # Calculate expected signature
        expected_signature = base64.b64encode(
            hmac.new(
                webhook_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')

        headers = {"X-Shopify-Hmac-Sha256": expected_signature}

        result = ShopifyClient.verify_webhook_signature(headers, body, webhook_secret)
        assert result is True

    def test_verify_webhook_signature_invalid(self):
        """Test invalid webhook signature verification"""
        webhook_secret = "test-secret"
        body = b'{"test": "data"}'
        headers = {"X-Shopify-Hmac-Sha256": "invalid-signature"}

        result = ShopifyClient.verify_webhook_signature(headers, body, webhook_secret)
        assert result is False

    def test_verify_webhook_signature_missing_header(self):
        """Test webhook signature verification with missing header"""
        webhook_secret = "test-secret"
        body = b'{"test": "data"}'
        headers = {}

        result = ShopifyClient.verify_webhook_signature(headers, body, webhook_secret)
        assert result is False

    @patch('server.src.utils.shopify_client.requests.Session.request')
    def test_test_connection_success(self, mock_request, client, mock_db, mock_store):
        """Test successful connection test"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "shop": {
                "id": 123,
                "name": "Test Store",
                "domain": "test-store.myshopify.com",
                "email": "test@example.com"
            }
        }
        mock_request.return_value = mock_response

        result = client.test_connection("test-store-id")

        assert result["name"] == "Test Store"
        assert result["domain"] == "test-store.myshopify.com"

    @patch('server.src.utils.shopify_client.requests.Session.request')
    def test_update_product_success(self, mock_request, client, mock_db, mock_store):
        """Test successful product update"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        update_data = {"title": "Updated Product Title"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "product": {
                "id": 123,
                "title": "Updated Product Title",
                "handle": "updated-product"
            }
        }
        mock_request.return_value = mock_response

        result = client.update_product("test-store-id", "123", update_data)

        assert result["id"] == 123
        assert result["title"] == "Updated Product Title"

    @patch('server.src.utils.shopify_client.requests.Session.request')
    def test_delete_product_success(self, mock_request, client, mock_db, mock_store):
        """Test successful product deletion"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        result = client.delete_product("test-store-id", "123")

        assert result is True

    @patch('server.src.utils.shopify_client.requests.Session.request')
    def test_get_orders_with_filters(self, mock_request, client, mock_db, mock_store):
        """Test orders fetching with date filter"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"orders": []}
        mock_request.return_value = mock_response

        since_time = datetime(2023, 1, 1, tzinfo=timezone.utc)
        client.get_orders("test-store-id", since_time=since_time, limit=50, status="open")

        # Verify the request was made with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        params = call_args[1]["params"]

        assert params["limit"] == 50
        assert params["status"] == "open"
        assert "created_at_min" in params

    @patch('server.src.utils.shopify_client.requests.Session.request')
    def test_max_retries_exceeded(self, mock_request, client, mock_db, mock_store):
        """Test behavior when max retries are exceeded"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        # Always return 429
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}
        mock_request.return_value = rate_limit_response

        with patch('time.sleep'):
            with pytest.raises(ShopifyRateLimitError):
                client.get_orders("test-store-id")

        # Should retry max_retries + 1 times (initial + retries)
        assert mock_request.call_count == client.MAX_RETRIES + 1