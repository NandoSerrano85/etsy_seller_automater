"""Comprehensive tests for Checkout and Payment API endpoints."""

import pytest
from fastapi import status
from unittest.mock import patch, Mock
import uuid


class TestCheckoutInitialization:
    """Tests for POST /api/storefront/checkout/init endpoint."""

    def test_init_checkout_with_valid_cart(self, client, sample_cart):
        """Test initializing checkout with valid cart."""
        response = client.post(
            "/api/storefront/checkout/init",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "United States",
                    "phone": "555-1234"
                },
                "guest_email": "guest@example.com"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "session_id" in data
        assert "cart_id" in data
        assert "subtotal" in data
        assert "tax" in data
        assert "shipping" in data
        assert "total" in data
        assert "shipping_address" in data
        assert "billing_address" in data

    def test_init_checkout_calculates_tax(self, client, sample_cart):
        """Test that checkout initialization calculates tax."""
        response = client.post(
            "/api/storefront/checkout/init",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "state": "NY",  # Should have NY tax
                    "zip_code": "10001",
                    "country": "United States"
                },
                "guest_email": "guest@example.com"
            }
        )

        data = response.json()

        assert data["tax"] > 0  # NY has sales tax

    def test_init_checkout_calculates_shipping(self, client, sample_cart):
        """Test that checkout initialization calculates shipping cost."""
        response = client.post(
            "/api/storefront/checkout/init",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "United States"
                },
                "guest_email": "guest@example.com"
            }
        )

        data = response.json()

        assert "shipping" in data
        assert data["shipping"] >= 0

    def test_init_checkout_uses_shipping_for_billing_if_not_provided(self, client, sample_cart):
        """Test that billing address defaults to shipping address."""
        shipping_address = {
            "first_name": "John",
            "last_name": "Doe",
            "address1": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "United States"
        }

        response = client.post(
            "/api/storefront/checkout/init",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={
                "shipping_address": shipping_address,
                "guest_email": "guest@example.com"
            }
        )

        data = response.json()

        assert data["billing_address"] == shipping_address

    def test_init_checkout_with_separate_billing_address(self, client, sample_cart):
        """Test checkout with different billing address."""
        response = client.post(
            "/api/storefront/checkout/init",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "United States"
                },
                "billing_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "456 Billing Ave",
                    "city": "Brooklyn",
                    "state": "NY",
                    "zip_code": "11201",
                    "country": "United States"
                },
                "guest_email": "guest@example.com"
            }
        )

        data = response.json()

        assert data["shipping_address"]["address1"] == "123 Main St"
        assert data["billing_address"]["address1"] == "456 Billing Ave"

    def test_init_checkout_empty_cart_returns_400(self, client):
        """Test checkout with empty cart returns error."""
        session_id = str(uuid.uuid4())

        response = client.post(
            "/api/storefront/checkout/init",
            headers={"X-Session-ID": session_id},
            json={
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "United States"
                },
                "guest_email": "guest@example.com"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "empty" in response.json()["detail"].lower()

    def test_init_checkout_guest_requires_email(self, client, sample_cart):
        """Test that guest checkout requires email."""
        response = client.post(
            "/api/storefront/checkout/init",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "United States"
                }
                # No guest_email provided
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestStripePaymentIntent:
    """Tests for POST /api/storefront/checkout/create-payment-intent endpoint."""

    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_success(self, mock_create, client):
        """Test creating Stripe PaymentIntent."""
        # Mock Stripe response
        mock_intent = Mock()
        mock_intent.client_secret = "pi_test_secret_123"
        mock_intent.id = "pi_test_123"
        mock_create.return_value = mock_intent

        response = client.post(
            "/api/storefront/checkout/create-payment-intent",
            json={
                "amount": 100.00,
                "currency": "usd"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "client_secret" in data
        assert "payment_intent_id" in data
        assert data["client_secret"] == "pi_test_secret_123"
        assert data["payment_intent_id"] == "pi_test_123"

        # Verify Stripe was called with correct amount (in cents)
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["amount"] == 10000  # $100 = 10000 cents

    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_with_different_currency(self, mock_create, client):
        """Test creating payment intent with different currency."""
        mock_intent = Mock()
        mock_intent.client_secret = "pi_test_secret"
        mock_intent.id = "pi_test"
        mock_create.return_value = mock_intent

        response = client.post(
            "/api/storefront/checkout/create-payment-intent",
            json={
                "amount": 50.00,
                "currency": "eur"
            }
        )

        assert response.status_code == status.HTTP_200_OK

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["currency"] == "eur"


class TestCheckoutCompletion:
    """Tests for POST /api/storefront/checkout/complete endpoint."""

    @patch('stripe.PaymentIntent.retrieve')
    def test_complete_checkout_creates_order(self, mock_retrieve, client, sample_cart, test_db):
        """Test that completing checkout creates an order."""
        # Mock successful payment
        mock_intent = Mock()
        mock_intent.status = "succeeded"
        mock_intent.id = "pi_test_123"
        mock_retrieve.return_value = mock_intent

        response = client.post(
            "/api/storefront/checkout/complete",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={
                "session_id": str(uuid.uuid4()),
                "payment_intent_id": "pi_test_123",
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "United States"
                },
                "guest_email": "guest@example.com"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "order_id" in data
        assert "order_number" in data
        assert "total" in data
        assert data["payment_status"] == "paid"
        assert "Order created successfully" in data["message"]

    @patch('stripe.PaymentIntent.retrieve')
    def test_complete_checkout_clears_cart(self, mock_retrieve, client, sample_cart, test_db):
        """Test that completing checkout clears the cart."""
        mock_intent = Mock()
        mock_intent.status = "succeeded"
        mock_retrieve.return_value = mock_intent

        # Complete checkout
        client.post(
            "/api/storefront/checkout/complete",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={
                "session_id": str(uuid.uuid4()),
                "payment_intent_id": "pi_test_123",
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "United States"
                },
                "guest_email": "guest@example.com"
            }
        )

        # Check cart is now empty
        test_db.refresh(sample_cart)
        assert sample_cart.items == []
        assert sample_cart.subtotal == 0
        assert sample_cart.is_active is False

    @patch('stripe.PaymentIntent.retrieve')
    def test_complete_checkout_updates_inventory(self, mock_retrieve, client, sample_cart, test_db, sample_uvdtf_cup_wrap):
        """Test that completing checkout updates inventory."""
        mock_intent = Mock()
        mock_intent.status = "succeeded"
        mock_retrieve.return_value = mock_intent

        initial_inventory = sample_uvdtf_cup_wrap.inventory_quantity

        # Complete checkout
        client.post(
            "/api/storefront/checkout/complete",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={
                "session_id": str(uuid.uuid4()),
                "payment_intent_id": "pi_test_123",
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "United States"
                },
                "guest_email": "guest@example.com"
            }
        )

        # Check inventory was decreased
        test_db.refresh(sample_uvdtf_cup_wrap)
        ordered_quantity = sample_cart.items[0]["quantity"]
        expected_inventory = initial_inventory - ordered_quantity

        assert sample_uvdtf_cup_wrap.inventory_quantity == expected_inventory

    @patch('stripe.PaymentIntent.retrieve')
    def test_complete_checkout_with_failed_payment(self, mock_retrieve, client, sample_cart):
        """Test completing checkout with failed payment."""
        # Mock failed payment
        mock_intent = Mock()
        mock_intent.status = "requires_payment_method"  # Failed
        mock_retrieve.return_value = mock_intent

        response = client.post(
            "/api/storefront/checkout/complete",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={
                "session_id": str(uuid.uuid4()),
                "payment_intent_id": "pi_test_failed",
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "United States"
                },
                "guest_email": "guest@example.com"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not successful" in response.json()["detail"].lower()


class TestCheckoutCalculations:
    """Tests for checkout price calculations."""

    def test_checkout_total_calculation(self, client, sample_cart):
        """Test that checkout calculates total correctly."""
        response = client.post(
            "/api/storefront/checkout/init",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "United States"
                },
                "guest_email": "guest@example.com"
            }
        )

        data = response.json()

        calculated_total = data["subtotal"] + data["tax"] + data["shipping"]
        assert round(calculated_total, 2) == data["total"]

    def test_checkout_free_shipping_over_threshold(self, client, test_db, sample_uvdtf_cup_wrap):
        """Test free shipping for orders over threshold."""
        from server.src.entities.ecommerce.cart import ShoppingCart

        # Create cart with high-value items (over $50)
        cart = ShoppingCart(
            id=uuid.uuid4(),
            session_id=f"free-ship-{uuid.uuid4()}",
            items=[
                {
                    "id": str(uuid.uuid4()),
                    "product_id": str(sample_uvdtf_cup_wrap.id),
                    "product_name": sample_uvdtf_cup_wrap.name,
                    "product_slug": sample_uvdtf_cup_wrap.slug,
                    "price": sample_uvdtf_cup_wrap.price,
                    "quantity": 5,  # $12.99 * 5 = $64.95
                    "subtotal": sample_uvdtf_cup_wrap.price * 5,
                    "image": sample_uvdtf_cup_wrap.featured_image
                }
            ],
            subtotal=sample_uvdtf_cup_wrap.price * 5,
            is_active=True
        )
        test_db.add(cart)
        test_db.commit()

        response = client.post(
            "/api/storefront/checkout/init",
            headers={"X-Session-ID": cart.session_id},
            json={
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "United States"
                },
                "guest_email": "guest@example.com"
            }
        )

        data = response.json()

        # Free shipping for orders over $50
        assert data["shipping"] == 0


class TestStripeWebhook:
    """Tests for POST /api/storefront/checkout/webhook endpoint."""

    @patch('stripe.Webhook.construct_event')
    def test_webhook_payment_success(self, mock_construct, client):
        """Test handling successful payment webhook."""
        # Mock webhook event
        mock_event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123"
                }
            }
        }
        mock_construct.return_value = mock_event

        response = client.post(
            "/api/storefront/checkout/webhook",
            headers={"stripe-signature": "test_signature"},
            content=b'{"test": "data"}'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    @patch('stripe.Webhook.construct_event')
    def test_webhook_payment_failed(self, mock_construct, client, test_db, sample_order):
        """Test handling failed payment webhook."""
        # Create order with pending payment
        sample_order.payment_id = "pi_test_fail"
        sample_order.payment_status = "pending"
        test_db.commit()

        # Mock webhook event
        mock_event = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_test_fail"
                }
            }
        }
        mock_construct.return_value = mock_event

        response = client.post(
            "/api/storefront/checkout/webhook",
            headers={"stripe-signature": "test_signature"},
            content=b'{"test": "data"}'
        )

        assert response.status_code == status.HTTP_200_OK

        # Check order was marked as failed
        test_db.refresh(sample_order)
        assert sample_order.payment_status == "failed"
        assert sample_order.status == "cancelled"

    def test_webhook_invalid_signature_rejected(self, client):
        """Test that webhooks with invalid signatures are rejected."""
        # No mocking - let it fail naturally
        response = client.post(
            "/api/storefront/checkout/webhook",
            headers={"stripe-signature": "invalid_signature"},
            content=b'{"test": "data"}'
        )

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
