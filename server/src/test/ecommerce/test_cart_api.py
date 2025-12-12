"""Comprehensive tests for Shopping Cart API endpoints."""

import pytest
from fastapi import status
import uuid


class TestGetCart:
    """Tests for GET /api/storefront/cart endpoint."""

    def test_get_cart_creates_new_cart_for_guest(self, client, test_db):
        """Test that getting cart creates a new one for guests."""
        session_id = str(uuid.uuid4())

        response = client.get(
            "/api/storefront/cart",
            headers={"X-Session-ID": session_id}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["items"] == []
        assert data["subtotal"] == 0
        assert data["item_count"] == 0

    def test_get_existing_cart_with_items(self, client, sample_cart):
        """Test getting existing cart with items."""
        response = client.get(
            "/api/storefront/cart",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["items"]) == 1
        assert data["subtotal"] > 0
        assert data["item_count"] == 1

    def test_get_cart_returns_correct_items(self, client, sample_cart):
        """Test cart returns correct item details."""
        response = client.get(
            "/api/storefront/cart",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        item = data["items"][0]
        assert "id" in item
        assert "product_id" in item
        assert "product_name" in item
        assert "price" in item
        assert "quantity" in item
        assert "subtotal" in item


class TestAddToCart:
    """Tests for POST /api/storefront/cart/add endpoint."""

    def test_add_product_to_empty_cart(self, client, sample_uvdtf_cup_wrap):
        """Test adding a product to empty cart."""
        session_id = str(uuid.uuid4())

        response = client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_id},
            json={
                "product_id": str(sample_uvdtf_cup_wrap.id),
                "quantity": 2
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 2
        assert data["subtotal"] == sample_uvdtf_cup_wrap.price * 2

    def test_add_product_with_variant(self, client, sample_uvdtf_cup_wrap, sample_product_variants):
        """Test adding product with variant."""
        variant = sample_product_variants[0]
        session_id = str(uuid.uuid4())

        response = client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_id},
            json={
                "product_id": str(sample_uvdtf_cup_wrap.id),
                "variant_id": str(variant.id),
                "quantity": 1
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["items"]) == 1
        assert data["items"][0]["variant_id"] == str(variant.id)
        assert data["items"][0]["variant_name"] == variant.name

    def test_add_same_product_increases_quantity(self, client, sample_uvdtf_cup_wrap):
        """Test adding same product again increases quantity."""
        session_id = str(uuid.uuid4())

        # Add product first time
        client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_id},
            json={
                "product_id": str(sample_uvdtf_cup_wrap.id),
                "quantity": 1
            }
        )

        # Add same product again
        response = client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_id},
            json={
                "product_id": str(sample_uvdtf_cup_wrap.id),
                "quantity": 2
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 3  # 1 + 2

    def test_add_different_products(self, client, sample_uvdtf_cup_wrap, sample_dtf_square):
        """Test adding multiple different products."""
        session_id = str(uuid.uuid4())

        # Add first product
        client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_id},
            json={
                "product_id": str(sample_uvdtf_cup_wrap.id),
                "quantity": 1
            }
        )

        # Add second product
        response = client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_id},
            json={
                "product_id": str(sample_dtf_square.id),
                "quantity": 1
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["items"]) == 2
        assert data["subtotal"] == sample_uvdtf_cup_wrap.price + sample_dtf_square.price

    def test_add_invalid_product_returns_404(self, client):
        """Test adding non-existent product returns 404."""
        session_id = str(uuid.uuid4())

        response = client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_id},
            json={
                "product_id": str(uuid.uuid4()),
                "quantity": 1
            }
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_inactive_product_returns_404(self, client, inactive_product):
        """Test adding inactive product returns 404."""
        session_id = str(uuid.uuid4())

        response = client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_id},
            json={
                "product_id": str(inactive_product.id),
                "quantity": 1
            }
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_with_invalid_quantity(self, client, sample_uvdtf_cup_wrap):
        """Test adding with invalid quantity."""
        session_id = str(uuid.uuid4())

        # Quantity = 0 should fail
        response = client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_id},
            json={
                "product_id": str(sample_uvdtf_cup_wrap.id),
                "quantity": 0
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdateCartItem:
    """Tests for PUT /api/storefront/cart/update/{item_id} endpoint."""

    def test_update_item_quantity(self, client, sample_cart):
        """Test updating cart item quantity."""
        item_id = sample_cart.items[0]["id"]

        response = client.put(
            f"/api/storefront/cart/update/{item_id}",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={"quantity": 5}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        updated_item = data["items"][0]
        assert updated_item["quantity"] == 5
        assert updated_item["subtotal"] == updated_item["price"] * 5

    def test_update_quantity_to_zero_removes_item(self, client, sample_cart):
        """Test setting quantity to 0 removes item."""
        item_id = sample_cart.items[0]["id"]

        response = client.put(
            f"/api/storefront/cart/update/{item_id}",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={"quantity": 0}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["items"]) == 0
        assert data["subtotal"] == 0

    def test_update_nonexistent_item_returns_404(self, client, sample_cart):
        """Test updating non-existent item returns 404."""
        fake_item_id = str(uuid.uuid4())

        response = client.put(
            f"/api/storefront/cart/update/{fake_item_id}",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={"quantity": 5}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRemoveFromCart:
    """Tests for DELETE /api/storefront/cart/remove/{item_id} endpoint."""

    def test_remove_item_from_cart(self, client, sample_cart):
        """Test removing an item from cart."""
        item_id = sample_cart.items[0]["id"]

        response = client.delete(
            f"/api/storefront/cart/remove/{item_id}",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["items"]) == 0
        assert data["subtotal"] == 0

    def test_remove_nonexistent_item_returns_404(self, client, sample_cart):
        """Test removing non-existent item returns 404."""
        fake_item_id = str(uuid.uuid4())

        response = client.delete(
            f"/api/storefront/cart/remove/{fake_item_id}",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestClearCart:
    """Tests for DELETE /api/storefront/cart/clear endpoint."""

    def test_clear_cart_removes_all_items(self, client, sample_cart):
        """Test clearing cart removes all items."""
        response = client.delete(
            "/api/storefront/cart/clear",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["items"]) == 0
        assert data["subtotal"] == 0
        assert data["item_count"] == 0

    def test_clear_empty_cart(self, client):
        """Test clearing already empty cart."""
        session_id = str(uuid.uuid4())

        response = client.delete(
            "/api/storefront/cart/clear",
            headers={"X-Session-ID": session_id}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["items"]) == 0


class TestCartCalculations:
    """Tests for cart total calculations."""

    def test_subtotal_calculation_single_item(self, client, sample_uvdtf_cup_wrap):
        """Test subtotal calculation with single item."""
        session_id = str(uuid.uuid4())

        response = client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_id},
            json={
                "product_id": str(sample_uvdtf_cup_wrap.id),
                "quantity": 3
            }
        )

        data = response.json()
        expected_subtotal = round(sample_uvdtf_cup_wrap.price * 3, 2)

        assert data["subtotal"] == expected_subtotal

    def test_subtotal_calculation_multiple_items(self, client, sample_uvdtf_cup_wrap, sample_dtf_square):
        """Test subtotal calculation with multiple items."""
        session_id = str(uuid.uuid4())

        # Add first product
        client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_id},
            json={
                "product_id": str(sample_uvdtf_cup_wrap.id),
                "quantity": 2
            }
        )

        # Add second product
        response = client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_id},
            json={
                "product_id": str(sample_dtf_square.id),
                "quantity": 3
            }
        )

        data = response.json()
        expected_subtotal = round(
            (sample_uvdtf_cup_wrap.price * 2) + (sample_dtf_square.price * 3),
            2
        )

        assert data["subtotal"] == expected_subtotal

    def test_item_subtotal_updates_on_quantity_change(self, client, sample_cart):
        """Test item subtotal updates when quantity changes."""
        item_id = sample_cart.items[0]["id"]
        item_price = sample_cart.items[0]["price"]

        response = client.put(
            f"/api/storefront/cart/update/{item_id}",
            headers={"X-Session-ID": sample_cart.session_id or "test-session"},
            json={"quantity": 7}
        )

        data = response.json()
        updated_item = data["items"][0]

        expected_subtotal = round(item_price * 7, 2)
        assert updated_item["subtotal"] == expected_subtotal
        assert data["subtotal"] == expected_subtotal


class TestGuestVsCustomerCarts:
    """Tests for guest vs authenticated customer carts."""

    def test_guest_cart_with_session_id(self, client, guest_cart):
        """Test guest cart is identified by session ID."""
        response = client.get(
            "/api/storefront/cart",
            headers={"X-Session-ID": guest_cart.session_id}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["items"]) > 0

    def test_different_session_ids_have_different_carts(self, client, sample_uvdtf_cup_wrap):
        """Test different session IDs maintain separate carts."""
        session_1 = str(uuid.uuid4())
        session_2 = str(uuid.uuid4())

        # Add to first cart
        client.post(
            "/api/storefront/cart/add",
            headers={"X-Session-ID": session_1},
            json={
                "product_id": str(sample_uvdtf_cup_wrap.id),
                "quantity": 1
            }
        )

        # Check second cart is empty
        response = client.get(
            "/api/storefront/cart",
            headers={"X-Session-ID": session_2}
        )

        data = response.json()
        assert len(data["items"]) == 0
