"""Comprehensive tests for Customer Authentication API endpoints."""

import pytest
from fastapi import status
import uuid


class TestCustomerRegistration:
    """Tests for POST /api/storefront/customers/register endpoint."""

    def test_register_new_customer(self, client):
        """Test successful customer registration."""
        response = client.post(
            "/api/storefront/customers/register",
            json={
                "email": "newcustomer@example.com",
                "password": "SecurePass123!",
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "555-9999",
                "accepts_marketing": True
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "customer" in data

        # Check customer data
        customer = data["customer"]
        assert customer["email"] == "newcustomer@example.com"
        assert customer["first_name"] == "Jane"
        assert customer["last_name"] == "Smith"
        assert customer["phone"] == "555-9999"
        assert customer["accepts_marketing"] is True
        assert "id" in customer

    def test_register_minimal_required_fields(self, client):
        """Test registration with minimal required fields."""
        response = client.post(
            "/api/storefront/customers/register",
            json={
                "email": "minimal@example.com",
                "password": "Password123",
                "first_name": "Min",
                "last_name": "User"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["customer"]["email"] == "minimal@example.com"
        assert data["customer"]["accepts_marketing"] is False  # Default

    def test_register_duplicate_email_returns_400(self, client, sample_customer):
        """Test registering with existing email returns error."""
        response = client.post(
            "/api/storefront/customers/register",
            json={
                "email": sample_customer.email,  # Existing email
                "password": "Password123",
                "first_name": "Test",
                "last_name": "User"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email_format(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/storefront/customers/register",
            json={
                "email": "not-an-email",
                "password": "Password123",
                "first_name": "Test",
                "last_name": "User"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_password(self, client):
        """Test registration with password less than 8 characters."""
        response = client.post(
            "/api/storefront/customers/register",
            json={
                "email": "test@example.com",
                "password": "short",  # Less than 8 chars
                "first_name": "Test",
                "last_name": "User"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCustomerLogin:
    """Tests for POST /api/storefront/customers/login endpoint."""

    def test_login_with_valid_credentials(self, client, test_db):
        """Test successful login with valid credentials."""
        from server.src.test.ecommerce.conftest import create_test_customer

        # Create customer with known password
        customer = create_test_customer(test_db, email="login@example.com")

        response = client.post(
            "/api/storefront/customers/login",
            json={
                "email": "login@example.com",
                "password": "password123"  # Default password from fixture
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert "customer" in data
        assert data["customer"]["email"] == "login@example.com"

    def test_login_with_wrong_password(self, client, test_db):
        """Test login with incorrect password."""
        from server.src.test.ecommerce.conftest import create_test_customer

        customer = create_test_customer(test_db, email="login2@example.com")

        response = client.post(
            "/api/storefront/customers/login",
            json={
                "email": "login2@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json()["detail"].lower()

    def test_login_with_nonexistent_email(self, client):
        """Test login with non-existent email."""
        response = client.post(
            "/api/storefront/customers/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_returns_jwt_token(self, client, test_db):
        """Test that login returns a valid JWT token."""
        from server.src.test.ecommerce.conftest import create_test_customer
        import jwt

        customer = create_test_customer(test_db, email="jwt@example.com")

        response = client.post(
            "/api/storefront/customers/login",
            json={
                "email": "jwt@example.com",
                "password": "password123"
            }
        )

        data = response.json()
        token = data["access_token"]

        # Verify it's a valid JWT
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded["email"] == "jwt@example.com"
        assert decoded["type"] == "ecommerce_customer"


class TestGetCustomerProfile:
    """Tests for GET /api/storefront/customers/me endpoint."""

    def test_get_profile_with_valid_token(self, client, sample_customer, auth_headers):
        """Test getting profile with valid authentication."""
        response = client.get(
            "/api/storefront/customers/me",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["email"] == sample_customer.email
        assert data["first_name"] == sample_customer.first_name
        assert data["last_name"] == sample_customer.last_name
        assert data["id"] == str(sample_customer.id)

    def test_get_profile_without_token(self, client):
        """Test getting profile without authentication token."""
        response = client.get("/api/storefront/customers/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateCustomerProfile:
    """Tests for PUT /api/storefront/customers/me endpoint."""

    def test_update_profile_first_name(self, client, sample_customer, auth_headers):
        """Test updating first name."""
        response = client.put(
            "/api/storefront/customers/me",
            headers=auth_headers,
            json={"first_name": "Updated"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["first_name"] == "Updated"
        assert data["last_name"] == sample_customer.last_name  # Unchanged

    def test_update_profile_multiple_fields(self, client, sample_customer, auth_headers):
        """Test updating multiple fields at once."""
        response = client.put(
            "/api/storefront/customers/me",
            headers=auth_headers,
            json={
                "first_name": "NewFirst",
                "last_name": "NewLast",
                "phone": "555-0000",
                "accepts_marketing": False
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["first_name"] == "NewFirst"
        assert data["last_name"] == "NewLast"
        assert data["phone"] == "555-0000"
        assert data["accepts_marketing"] is False

    def test_update_profile_without_auth(self, client):
        """Test updating profile without authentication."""
        response = client.put(
            "/api/storefront/customers/me",
            json={"first_name": "Hacker"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestChangePassword:
    """Tests for POST /api/storefront/customers/me/change-password endpoint."""

    def test_change_password_with_correct_current(self, client, test_db, auth_headers):
        """Test changing password with correct current password."""
        from server.src.test.ecommerce.conftest import create_test_customer

        customer = create_test_customer(test_db, email="change@example.com")

        # Generate auth token for this customer
        import jwt
        from datetime import datetime, timedelta
        import os

        SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'test-secret-key')
        expires_delta = timedelta(minutes=60)
        expire = datetime.utcnow() + expires_delta

        to_encode = {
            "sub": str(customer.id),
            "email": customer.email,
            "exp": expire,
            "type": "ecommerce_customer"
        }

        token = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/api/storefront/customers/me/change-password",
            headers=headers,
            json={
                "current_password": "password123",
                "new_password": "NewSecurePass456!"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        assert "success" in response.json()["message"].lower()

    def test_change_password_with_wrong_current(self, client, auth_headers):
        """Test changing password with incorrect current password."""
        response = client.post(
            "/api/storefront/customers/me/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "NewPassword123"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "incorrect" in response.json()["detail"].lower()


class TestAddressManagement:
    """Tests for customer address management endpoints."""

    def test_get_customer_addresses(self, client, sample_customer_addresses, auth_headers):
        """Test getting customer addresses."""
        response = client.get(
            "/api/storefront/customers/me/addresses",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 2  # Shipping + billing from fixture

    def test_add_new_address(self, client, auth_headers):
        """Test adding a new address."""
        response = client.post(
            "/api/storefront/customers/me/addresses",
            headers=auth_headers,
            json={
                "first_name": "John",
                "last_name": "Doe",
                "address1": "789 New St",
                "city": "Chicago",
                "state": "IL",
                "zip_code": "60601",
                "country": "United States",
                "is_default_shipping": False,
                "is_default_billing": False
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["address1"] == "789 New St"
        assert data["city"] == "Chicago"
        assert "id" in data

    def test_add_address_as_default_shipping(self, client, auth_headers, sample_customer_addresses):
        """Test adding address as default shipping."""
        response = client.post(
            "/api/storefront/customers/me/addresses",
            headers=auth_headers,
            json={
                "first_name": "John",
                "last_name": "Doe",
                "address1": "999 Default St",
                "city": "Boston",
                "state": "MA",
                "zip_code": "02101",
                "country": "United States",
                "is_default_shipping": True,
                "is_default_billing": False
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["is_default_shipping"] is True

    def test_update_address(self, client, auth_headers, sample_customer_addresses):
        """Test updating an existing address."""
        address = sample_customer_addresses[0]

        response = client.put(
            f"/api/storefront/customers/me/addresses/{address.id}",
            headers=auth_headers,
            json={
                "first_name": "John",
                "last_name": "Doe",
                "address1": "123 Updated St",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
                "country": "United States",
                "is_default_shipping": True,
                "is_default_billing": False
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["address1"] == "123 Updated St"

    def test_delete_address(self, client, auth_headers, sample_customer_addresses):
        """Test deleting an address."""
        address = sample_customer_addresses[1]  # Use billing address

        response = client.delete(
            f"/api/storefront/customers/me/addresses/{address.id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_nonexistent_address_returns_404(self, client, auth_headers):
        """Test deleting non-existent address."""
        fake_id = str(uuid.uuid4())

        response = client.delete(
            f"/api/storefront/customers/me/addresses/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAuthenticationSecurity:
    """Tests for authentication security features."""

    def test_expired_token_rejected(self, client):
        """Test that expired tokens are rejected."""
        import jwt
        from datetime import datetime, timedelta
        import os

        SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'test-secret-key')

        # Create expired token
        expire = datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago

        to_encode = {
            "sub": str(uuid.uuid4()),
            "email": "test@example.com",
            "exp": expire,
            "type": "ecommerce_customer"
        }

        expired_token = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = client.get(
            "/api/storefront/customers/me",
            headers=headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token_signature_rejected(self, client):
        """Test that tokens with invalid signatures are rejected."""
        import jwt
        from datetime import datetime, timedelta

        # Create token with wrong secret
        expire = datetime.utcnow() + timedelta(hours=1)

        to_encode = {
            "sub": str(uuid.uuid4()),
            "email": "test@example.com",
            "exp": expire,
            "type": "ecommerce_customer"
        }

        invalid_token = jwt.encode(to_encode, "wrong-secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {invalid_token}"}

        response = client.get(
            "/api/storefront/customers/me",
            headers=headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_malformed_token_rejected(self, client):
        """Test that malformed tokens are rejected."""
        headers = {"Authorization": "Bearer not-a-valid-jwt"}

        response = client.get(
            "/api/storefront/customers/me",
            headers=headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
