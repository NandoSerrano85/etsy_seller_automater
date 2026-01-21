"""Comprehensive tests for Orders API endpoints."""

import pytest
from fastapi import status
import uuid


class TestGetCustomerOrders:
    """Tests for GET /api/storefront/orders endpoint."""

    def test_get_customer_orders(self, client, sample_order, auth_headers):
        """Test getting customer's order list."""
        response = client.get(
            "/api/storefront/orders",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["order_number"] == sample_order.order_number

    def test_get_orders_with_pagination(self, client, auth_headers, test_db, sample_customer, sample_uvdtf_cup_wrap):
        """Test pagination on orders list."""
        from server.src.entities.ecommerce.order import Order

        # Create multiple orders
        for i in range(5):
            order = Order(
                id=uuid.uuid4(),
                order_number=f"ORD-TEST-{i}",
                customer_id=sample_customer.id,
                subtotal=10.00,
                tax=1.00,
                shipping=5.00,
                total=16.00,
                shipping_address={},
                billing_address={},
                payment_status="paid",
                status="processing"
            )
            test_db.add(order)
        test_db.commit()

        # Get first 3 orders
        response = client.get(
            "/api/storefront/orders?limit=3&offset=0",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    def test_get_orders_filter_by_status(self, client, auth_headers, test_db, sample_customer):
        """Test filtering orders by status."""
        from server.src.entities.ecommerce.order import Order

        # Create orders with different statuses
        for status_val in ["processing", "completed", "cancelled"]:
            order = Order(
                id=uuid.uuid4(),
                order_number=f"ORD-{status_val.upper()}",
                customer_id=sample_customer.id,
                subtotal=10.00,
                tax=1.00,
                shipping=5.00,
                total=16.00,
                shipping_address={},
                billing_address={},
                payment_status="paid",
                status=status_val
            )
            test_db.add(order)
        test_db.commit()

        # Filter for completed orders only
        response = client.get(
            "/api/storefront/orders?status=completed",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert all(order["status"] == "completed" for order in data)

    def test_get_orders_without_auth_returns_403(self, client):
        """Test getting orders without authentication."""
        response = client.get("/api/storefront/orders")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetOrderDetails:
    """Tests for GET /api/storefront/orders/{order_id} endpoint."""

    def test_get_order_details_by_id(self, client, sample_order, auth_headers):
        """Test getting full order details by ID."""
        response = client.get(
            f"/api/storefront/orders/{sample_order.id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == str(sample_order.id)
        assert data["order_number"] == sample_order.order_number
        assert data["subtotal"] == sample_order.subtotal
        assert data["total"] == sample_order.total
        assert "items" in data
        assert len(data["items"]) >= 1
        assert "shipping_address" in data

    def test_get_order_details_by_number(self, client, sample_order, auth_headers):
        """Test getting order by order number."""
        response = client.get(
            f"/api/storefront/orders/number/{sample_order.order_number}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["order_number"] == sample_order.order_number

    def test_get_other_customers_order_returns_404(self, client, sample_order, test_db):
        """Test that customer cannot view another customer's order."""
        from server.src.test.ecommerce.conftest import create_test_customer
        import jwt
        from datetime import datetime, timedelta
        import os

        # Create different customer
        other_customer = create_test_customer(test_db, email="other@example.com")

        # Create token for other customer
        SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'test-secret-key')
        expires_delta = timedelta(minutes=60)
        expire = datetime.utcnow() + expires_delta

        to_encode = {
            "sub": str(other_customer.id),
            "email": other_customer.email,
            "exp": expire,
            "type": "ecommerce_customer"
        }

        token = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}

        # Try to get sample_order (belongs to different customer)
        response = client.get(
            f"/api/storefront/orders/{sample_order.id}",
            headers=headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_nonexistent_order_returns_404(self, client, auth_headers):
        """Test getting non-existent order."""
        fake_id = str(uuid.uuid4())

        response = client.get(
            f"/api/storefront/orders/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGuestOrderLookup:
    """Tests for GET /api/storefront/orders/guest/lookup endpoint."""

    def test_guest_order_lookup_success(self, client, guest_order):
        """Test successful guest order lookup."""
        response = client.get(
            f"/api/storefront/orders/guest/lookup?order_number={guest_order.order_number}&email={guest_order.guest_email}"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["order_number"] == guest_order.order_number
        assert data["guest_email"] == guest_order.guest_email

    def test_guest_order_lookup_wrong_email(self, client, guest_order):
        """Test guest order lookup with wrong email."""
        response = client.get(
            f"/api/storefront/orders/guest/lookup?order_number={guest_order.order_number}&email=wrong@example.com"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_guest_order_lookup_wrong_order_number(self, client, guest_order):
        """Test guest order lookup with wrong order number."""
        response = client.get(
            f"/api/storefront/orders/guest/lookup?order_number=WRONG-123&email={guest_order.guest_email}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_guest_order_lookup_no_auth_required(self, client, guest_order):
        """Test that guest order lookup doesn't require authentication."""
        # Don't send auth headers
        response = client.get(
            f"/api/storefront/orders/guest/lookup?order_number={guest_order.order_number}&email={guest_order.guest_email}"
        )

        assert response.status_code == status.HTTP_200_OK


class TestOrderItemDetails:
    """Tests for order item details."""

    def test_order_includes_item_details(self, client, sample_order, auth_headers):
        """Test that order details include item information."""
        response = client.get(
            f"/api/storefront/orders/{sample_order.id}",
            headers=auth_headers
        )

        data = response.json()
        items = data["items"]

        assert len(items) >= 1
        item = items[0]

        assert "product_name" in item
        assert "price" in item
        assert "quantity" in item
        assert "total" in item
        assert item["total"] == item["price"] * item["quantity"]

    def test_order_shows_fulfillment_status(self, client, sample_order, auth_headers):
        """Test that order shows fulfillment status."""
        response = client.get(
            f"/api/storefront/orders/{sample_order.id}",
            headers=auth_headers
        )

        data = response.json()

        assert "fulfillment_status" in data
        assert data["fulfillment_status"] in ["unfulfilled", "fulfilled", "shipped"]
        assert "payment_status" in data
        assert data["payment_status"] in ["pending", "paid", "failed", "refunded"]


class TestDigitalProductDownload:
    """Tests for GET /api/storefront/orders/{id}/items/{item_id}/download endpoint."""

    def test_download_digital_product(self, client, test_db, sample_customer, sample_digital_product, auth_headers):
        """Test downloading a digital product from order."""
        from server.src.entities.ecommerce.order import Order, OrderItem

        # Create order with digital product
        order = Order(
            id=uuid.uuid4(),
            order_number=f"ORD-DIGITAL-{uuid.uuid4().hex[:8].upper()}",
            customer_id=sample_customer.id,
            subtotal=24.99,
            tax=2.00,
            shipping=0,
            total=26.99,
            shipping_address={},
            billing_address={},
            payment_status="paid",
            status="processing"
        )
        test_db.add(order)
        test_db.flush()

        # Add digital product item
        order_item = OrderItem(
            id=uuid.uuid4(),
            order_id=order.id,
            product_id=sample_digital_product.id,
            product_name=sample_digital_product.name,
            price=24.99,
            quantity=1,
            total=24.99,
            download_url="https://example.com/downloads/file.zip",
            download_count=0
        )
        test_db.add(order_item)
        test_db.commit()
        test_db.refresh(order)

        # Download the digital product
        response = client.get(
            f"/api/storefront/orders/{order.id}/items/{order_item.id}/download",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "download_url" in data
        assert data["download_url"] == "https://example.com/downloads/file.zip"
        assert "download_count" in data
        assert data["download_count"] == 1  # Incremented

    def test_download_non_digital_product_returns_400(self, client, sample_order, auth_headers):
        """Test downloading a non-digital product returns error."""
        # sample_order has physical product
        item_id = sample_order.items[0].id

        response = client.get(
            f"/api/storefront/orders/{sample_order.id}/items/{item_id}/download",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not a digital product" in response.json()["detail"].lower()


class TestAdminOrderFulfillment:
    """Tests for admin order fulfillment endpoints."""

    def test_fulfill_order(self, client, sample_order):
        """Test marking order as fulfilled."""
        # TODO: Add admin authentication
        response = client.put(
            f"/api/storefront/orders/{sample_order.id}/fulfill",
            json={
                "tracking_number": "1Z999AA10123456784",
                "tracking_url": "https://wwwapps.ups.com/tracking/tracking.html?tracknum=1Z999AA10123456784"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["fulfillment_status"] == "fulfilled"
        assert data["tracking_number"] == "1Z999AA10123456784"
        assert "shipped_at" in data

    def test_cancel_order(self, client, sample_order):
        """Test canceling an order."""
        # TODO: Add admin authentication
        response = client.put(
            f"/api/storefront/orders/{sample_order.id}/cancel",
            json={
                "cancel_reason": "Customer requested cancellation"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "cancelled"
        assert "cancelled_at" in data
        assert data["cancel_reason"] == "Customer requested cancellation"

    def test_cannot_cancel_shipped_order(self, client, test_db, sample_order):
        """Test that shipped orders cannot be cancelled."""
        # Mark order as shipped
        sample_order.fulfillment_status = "shipped"
        test_db.commit()

        response = client.put(
            f"/api/storefront/orders/{sample_order.id}/cancel",
            json={
                "cancel_reason": "Test cancellation"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot cancel shipped" in response.json()["detail"].lower()


class TestOrderCalculations:
    """Tests for order total calculations."""

    def test_order_total_equals_subtotal_plus_tax_plus_shipping(self, client, sample_order, auth_headers):
        """Test order total calculation."""
        response = client.get(
            f"/api/storefront/orders/{sample_order.id}",
            headers=auth_headers
        )

        data = response.json()

        calculated_total = data["subtotal"] + data["tax"] + data["shipping"] - data["discount"]
        assert round(calculated_total, 2) == data["total"]

    def test_order_subtotal_equals_sum_of_items(self, client, sample_order, auth_headers):
        """Test order subtotal equals sum of item totals."""
        response = client.get(
            f"/api/storefront/orders/{sample_order.id}",
            headers=auth_headers
        )

        data = response.json()
        items_total = sum(item["total"] for item in data["items"])

        assert round(items_total, 2) == data["subtotal"]


class TestOrderListResponse:
    """Tests for order list response format."""

    def test_order_list_has_simplified_format(self, client, sample_order, auth_headers):
        """Test that order list returns simplified response."""
        response = client.get(
            "/api/storefront/orders",
            headers=auth_headers
        )

        data = response.json()
        order = data[0]

        # Should have these fields
        assert "id" in order
        assert "order_number" in order
        assert "total" in order
        assert "status" in order
        assert "payment_status" in order
        assert "fulfillment_status" in order
        assert "item_count" in order
        assert "created_at" in order

    def test_order_list_sorted_by_most_recent(self, client, auth_headers, test_db, sample_customer):
        """Test that orders are sorted by creation date (newest first)."""
        from server.src.entities.ecommerce.order import Order
        from datetime import datetime, timedelta

        # Create orders with different dates
        old_order = Order(
            id=uuid.uuid4(),
            order_number="ORD-OLD",
            customer_id=sample_customer.id,
            subtotal=10.00,
            tax=1.00,
            shipping=5.00,
            total=16.00,
            shipping_address={},
            billing_address={},
            payment_status="paid",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=5)
        )

        recent_order = Order(
            id=uuid.uuid4(),
            order_number="ORD-RECENT",
            customer_id=sample_customer.id,
            subtotal=10.00,
            tax=1.00,
            shipping=5.00,
            total=16.00,
            shipping_address={},
            billing_address={},
            payment_status="paid",
            status="processing",
            created_at=datetime.utcnow()
        )

        test_db.add_all([old_order, recent_order])
        test_db.commit()

        response = client.get(
            "/api/storefront/orders",
            headers=auth_headers
        )

        data = response.json()

        # First order should be the most recent
        assert data[0]["order_number"] == "ORD-RECENT"
