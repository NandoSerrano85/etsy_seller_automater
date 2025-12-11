"""Comprehensive tests for Products API endpoints."""

import pytest
from fastapi import status
import uuid


class TestListProducts:
    """Tests for GET /api/storefront/products endpoint."""

    def test_list_all_products(self, client, multiple_products):
        """Test listing all active products."""
        response = client.get("/api/storefront/products")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10  # 5 UVDTF + 3 DTF + 2 Sublimation

    def test_list_products_with_pagination(self, client, multiple_products):
        """Test pagination parameters."""
        # Get first 5 products
        response = client.get("/api/storefront/products?limit=5&offset=0")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5

        # Get next 5 products
        response = client.get("/api/storefront/products?limit=5&offset=5")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5

    def test_filter_by_print_method_uvdtf(self, client, multiple_products):
        """Test filtering by UVDTF print method."""
        response = client.get("/api/storefront/products?print_method=uvdtf")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5  # 5 UVDTF products
        assert all(p["print_method"] == "uvdtf" for p in data)

    def test_filter_by_print_method_dtf(self, client, multiple_products):
        """Test filtering by DTF print method."""
        response = client.get("/api/storefront/products?print_method=dtf")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3  # 3 DTF products
        assert all(p["print_method"] == "dtf" for p in data)

    def test_filter_by_print_method_sublimation(self, client, multiple_products):
        """Test filtering by sublimation print method."""
        response = client.get("/api/storefront/products?print_method=sublimation")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2  # 2 Sublimation products
        assert all(p["print_method"] == "sublimation" for p in data)

    def test_filter_by_category_cup_wraps(self, client, multiple_products):
        """Test filtering by cup_wraps category."""
        response = client.get("/api/storefront/products?category=cup_wraps")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 3 UVDTF cup_wraps (even indexed) + 2 sublimation = 5
        assert len(data) == 5
        assert all(p["category"] == "cup_wraps" for p in data)

    def test_filter_by_category_single_square(self, client, multiple_products):
        """Test filtering by single_square category."""
        response = client.get("/api/storefront/products?category=single_square")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3  # 3 DTF single_square
        assert all(p["category"] == "single_square" for p in data)

    def test_filter_by_print_method_and_category(self, client, multiple_products):
        """Test filtering by both print method and category."""
        response = client.get("/api/storefront/products?print_method=uvdtf&category=cup_wraps")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3  # UVDTF products with category cup_wraps
        assert all(p["print_method"] == "uvdtf" for p in data)
        assert all(p["category"] == "cup_wraps" for p in data)

    def test_filter_by_featured(self, client, multiple_products):
        """Test filtering featured products."""
        response = client.get("/api/storefront/products?featured=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1  # Only first UVDTF product is featured
        assert data[0]["is_featured"] is True

    def test_search_products(self, client, multiple_products):
        """Test search functionality."""
        response = client.get("/api/storefront/products?search=UVDTF")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5  # All UVDTF products
        assert all("UVDTF" in p["name"] for p in data)

    def test_inactive_products_not_listed(self, client, inactive_product):
        """Test that inactive products are not listed."""
        response = client.get("/api/storefront/products")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0  # Inactive product should not appear

    def test_empty_results(self, client):
        """Test empty results when no products match."""
        response = client.get("/api/storefront/products?print_method=vinyl")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0


class TestGetProductsByPrintMethod:
    """Tests for GET /api/storefront/products/print-method/{method} endpoint."""

    def test_get_uvdtf_products(self, client, multiple_products):
        """Test getting products by UVDTF print method."""
        response = client.get("/api/storefront/products/print-method/uvdtf")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5
        assert all(p["print_method"] == "uvdtf" for p in data)

    def test_get_dtf_products(self, client, multiple_products):
        """Test getting products by DTF print method."""
        response = client.get("/api/storefront/products/print-method/dtf")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert all(p["print_method"] == "dtf" for p in data)

    def test_get_products_with_pagination(self, client, multiple_products):
        """Test pagination for print method endpoint."""
        response = client.get("/api/storefront/products/print-method/uvdtf?limit=3&offset=0")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    def test_nonexistent_print_method(self, client, multiple_products):
        """Test with non-existent print method returns empty list."""
        response = client.get("/api/storefront/products/print-method/nonexistent")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0


class TestGetProductsByCategory:
    """Tests for GET /api/storefront/products/category/{category} endpoint."""

    def test_get_cup_wraps_products(self, client, multiple_products):
        """Test getting cup wraps products."""
        response = client.get("/api/storefront/products/category/cup_wraps")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5  # 3 UVDTF + 2 Sublimation
        assert all(p["category"] == "cup_wraps" for p in data)

    def test_get_single_square_products(self, client, multiple_products):
        """Test getting single square products."""
        response = client.get("/api/storefront/products/category/single_square")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3  # 3 DTF
        assert all(p["category"] == "single_square" for p in data)

    def test_get_single_rectangle_products(self, client, multiple_products):
        """Test getting single rectangle products."""
        response = client.get("/api/storefront/products/category/single_rectangle")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2  # 2 UVDTF
        assert all(p["category"] == "single_rectangle" for p in data)

    def test_get_products_with_pagination(self, client, multiple_products):
        """Test pagination for category endpoint."""
        response = client.get("/api/storefront/products/category/cup_wraps?limit=2&offset=0")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_nonexistent_category(self, client, multiple_products):
        """Test with non-existent category returns empty list."""
        response = client.get("/api/storefront/products/category/nonexistent")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0


class TestSearchProducts:
    """Tests for GET /api/storefront/products/search endpoint."""

    def test_search_by_name(self, client, sample_uvdtf_cup_wrap):
        """Test searching by product name."""
        response = client.get("/api/storefront/products/search?q=Floral")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert "Floral" in data[0]["name"]

    def test_search_by_description(self, client, sample_dtf_square):
        """Test searching by product description."""
        response = client.get("/api/storefront/products/search?q=DTF")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any("DTF" in p["name"] or "DTF" in p.get("short_description", "") for p in data)

    def test_search_case_insensitive(self, client, sample_uvdtf_cup_wrap):
        """Test that search is case insensitive."""
        response1 = client.get("/api/storefront/products/search?q=floral")
        response2 = client.get("/api/storefront/products/search?q=FLORAL")
        response3 = client.get("/api/storefront/products/search?q=Floral")

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response3.status_code == status.HTTP_200_OK

        assert len(response1.json()) == len(response2.json()) == len(response3.json())

    def test_search_no_results(self, client, sample_uvdtf_cup_wrap):
        """Test search with no matching results."""
        response = client.get("/api/storefront/products/search?q=nonexistent")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    def test_search_min_length_validation(self, client):
        """Test search query must be at least 2 characters."""
        response = client.get("/api/storefront/products/search?q=a")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_with_limit(self, client, multiple_products):
        """Test search with result limit."""
        response = client.get("/api/storefront/products/search?q=Product&limit=3")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3


class TestGetProductBySlug:
    """Tests for GET /api/storefront/products/{slug} endpoint."""

    def test_get_product_by_slug(self, client, sample_uvdtf_cup_wrap):
        """Test getting a product by slug."""
        response = client.get(f"/api/storefront/products/{sample_uvdtf_cup_wrap.slug}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_uvdtf_cup_wrap.id)
        assert data["slug"] == sample_uvdtf_cup_wrap.slug
        assert data["name"] == sample_uvdtf_cup_wrap.name
        assert data["price"] == sample_uvdtf_cup_wrap.price
        assert data["print_method"] == sample_uvdtf_cup_wrap.print_method
        assert data["category"] == sample_uvdtf_cup_wrap.category

    def test_get_product_includes_variants(self, client, sample_uvdtf_cup_wrap, sample_product_variants):
        """Test that product detail includes variants."""
        response = client.get(f"/api/storefront/products/{sample_uvdtf_cup_wrap.slug}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["has_variants"] is True
        assert "variants" in data
        assert len(data["variants"]) == 2
        assert data["variants"][0]["name"] in ["16oz", "12oz"]

    def test_get_digital_product(self, client, sample_digital_product):
        """Test getting a digital product."""
        response = client.get(f"/api/storefront/products/{sample_digital_product.slug}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["product_type"] == "digital"
        assert data["print_method"] == "digital"
        assert "digital_file_url" in data
        assert data["download_limit"] == 3

    def test_get_nonexistent_product(self, client):
        """Test getting a non-existent product."""
        response = client.get("/api/storefront/products/nonexistent-slug")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_get_inactive_product_by_slug(self, client, inactive_product):
        """Test that inactive products return 404."""
        response = client.get(f"/api/storefront/products/{inactive_product.slug}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetProductById:
    """Tests for GET /api/storefront/products/id/{product_id} endpoint."""

    def test_get_product_by_id(self, client, sample_uvdtf_cup_wrap):
        """Test getting a product by ID."""
        response = client.get(f"/api/storefront/products/id/{sample_uvdtf_cup_wrap.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_uvdtf_cup_wrap.id)
        assert data["slug"] == sample_uvdtf_cup_wrap.slug

    def test_get_product_invalid_uuid(self, client):
        """Test with invalid UUID format."""
        response = client.get("/api/storefront/products/id/invalid-uuid")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.json()["detail"].lower()

    def test_get_nonexistent_product_id(self, client):
        """Test getting a non-existent product by ID."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/storefront/products/id/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_inactive_product_by_id(self, client, inactive_product):
        """Test that inactive products return 404."""
        response = client.get(f"/api/storefront/products/id/{inactive_product.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCreateProduct:
    """Tests for POST /api/storefront/products endpoint."""

    def test_create_physical_product(self, client, test_db):
        """Test creating a new physical product."""
        product_data = {
            "name": "New UVDTF Cup Wrap",
            "slug": "new-uvdtf-cup-wrap",
            "description": "A new UVDTF cup wrap product",
            "short_description": "New UVDTF wrap",
            "product_type": "physical",
            "print_method": "uvdtf",
            "category": "cup_wraps",
            "price": 14.99,
            "compare_at_price": 19.99,
            "cost": 6.00,
            "track_inventory": True,
            "inventory_quantity": 25,
            "allow_backorder": False,
            "images": ["https://example.com/new-image.jpg"],
            "featured_image": "https://example.com/new-featured.jpg",
            "meta_title": "New UVDTF Cup Wrap",
            "meta_description": "New cup wrap product",
            "is_active": True,
            "is_featured": False
        }

        response = client.post("/api/storefront/products", json=product_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == product_data["name"]
        assert data["slug"] == product_data["slug"]
        assert data["price"] == product_data["price"]
        assert data["print_method"] == product_data["print_method"]
        assert data["category"] == product_data["category"]
        assert "id" in data

    def test_create_digital_product(self, client, test_db):
        """Test creating a new digital product."""
        product_data = {
            "name": "Digital Design Bundle",
            "slug": "digital-design-bundle",
            "description": "Collection of digital designs",
            "product_type": "digital",
            "print_method": "digital",
            "category": "other_custom",
            "price": 29.99,
            "digital_file_url": "https://example.com/downloads/bundle.zip",
            "download_limit": 5,
            "is_active": True
        }

        response = client.post("/api/storefront/products", json=product_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["product_type"] == "digital"
        assert data["digital_file_url"] == product_data["digital_file_url"]
        assert data["download_limit"] == 5

    def test_create_product_duplicate_slug(self, client, sample_uvdtf_cup_wrap):
        """Test that creating a product with duplicate slug fails."""
        product_data = {
            "name": "Duplicate Product",
            "slug": sample_uvdtf_cup_wrap.slug,  # Duplicate slug
            "product_type": "physical",
            "print_method": "uvdtf",
            "category": "cup_wraps",
            "price": 9.99
        }

        response = client.post("/api/storefront/products", json=product_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_create_product_invalid_product_type(self, client):
        """Test creating a product with invalid product type."""
        product_data = {
            "name": "Invalid Product",
            "slug": "invalid-product",
            "product_type": "invalid_type",
            "print_method": "uvdtf",
            "category": "cup_wraps",
            "price": 9.99
        }

        response = client.post("/api/storefront/products", json=product_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid product_type" in response.json()["detail"].lower()

    def test_create_product_invalid_print_method(self, client):
        """Test creating a product with invalid print method."""
        product_data = {
            "name": "Invalid Product",
            "slug": "invalid-product",
            "product_type": "physical",
            "print_method": "invalid_method",
            "category": "cup_wraps",
            "price": 9.99
        }

        response = client.post("/api/storefront/products", json=product_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid print_method" in response.json()["detail"].lower()

    def test_create_product_invalid_category(self, client):
        """Test creating a product with invalid category."""
        product_data = {
            "name": "Invalid Product",
            "slug": "invalid-product",
            "product_type": "physical",
            "print_method": "uvdtf",
            "category": "invalid_category",
            "price": 9.99
        }

        response = client.post("/api/storefront/products", json=product_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid category" in response.json()["detail"].lower()

    def test_create_product_missing_required_fields(self, client):
        """Test creating a product with missing required fields."""
        product_data = {
            "name": "Incomplete Product",
            "slug": "incomplete-product"
            # Missing product_type, print_method, category, price
        }

        response = client.post("/api/storefront/products", json=product_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdateProduct:
    """Tests for PUT /api/storefront/products/{product_id} endpoint."""

    def test_update_product(self, client, sample_uvdtf_cup_wrap):
        """Test updating a product."""
        update_data = {
            "name": "Updated Cup Wrap Name",
            "slug": sample_uvdtf_cup_wrap.slug,
            "description": "Updated description",
            "short_description": "Updated short description",
            "product_type": sample_uvdtf_cup_wrap.product_type,
            "print_method": sample_uvdtf_cup_wrap.print_method,
            "category": sample_uvdtf_cup_wrap.category,
            "price": 16.99,
            "compare_at_price": 21.99,
            "is_featured": True
        }

        response = client.put(
            f"/api/storefront/products/{sample_uvdtf_cup_wrap.id}",
            json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["price"] == update_data["price"]
        assert data["description"] == update_data["description"]

    def test_update_product_slug(self, client, sample_uvdtf_cup_wrap):
        """Test updating product slug."""
        update_data = {
            "name": sample_uvdtf_cup_wrap.name,
            "slug": "new-updated-slug",
            "product_type": sample_uvdtf_cup_wrap.product_type,
            "print_method": sample_uvdtf_cup_wrap.print_method,
            "category": sample_uvdtf_cup_wrap.category,
            "price": sample_uvdtf_cup_wrap.price
        }

        response = client.put(
            f"/api/storefront/products/{sample_uvdtf_cup_wrap.id}",
            json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["slug"] == "new-updated-slug"

    def test_update_product_duplicate_slug(self, client, sample_uvdtf_cup_wrap, sample_dtf_square):
        """Test updating with duplicate slug fails."""
        update_data = {
            "name": "Test",
            "slug": sample_dtf_square.slug,  # Trying to use another product's slug
            "product_type": "physical",
            "print_method": "uvdtf",
            "category": "cup_wraps",
            "price": 9.99
        }

        response = client.put(
            f"/api/storefront/products/{sample_uvdtf_cup_wrap.id}",
            json=update_data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_update_nonexistent_product(self, client):
        """Test updating a non-existent product."""
        fake_id = str(uuid.uuid4())
        update_data = {
            "name": "Test",
            "slug": "test",
            "product_type": "physical",
            "print_method": "uvdtf",
            "category": "cup_wraps",
            "price": 9.99
        }

        response = client.put(f"/api/storefront/products/{fake_id}", json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_product_invalid_uuid(self, client):
        """Test updating with invalid UUID."""
        update_data = {
            "name": "Test",
            "slug": "test",
            "product_type": "physical",
            "print_method": "uvdtf",
            "category": "cup_wraps",
            "price": 9.99
        }

        response = client.put("/api/storefront/products/invalid-uuid", json=update_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDeleteProduct:
    """Tests for DELETE /api/storefront/products/{product_id} endpoint."""

    def test_delete_product(self, client, sample_uvdtf_cup_wrap, test_db):
        """Test deleting (soft delete) a product."""
        response = client.delete(f"/api/storefront/products/{sample_uvdtf_cup_wrap.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify product is soft deleted
        test_db.refresh(sample_uvdtf_cup_wrap)
        assert sample_uvdtf_cup_wrap.is_active is False

        # Verify product no longer appears in list
        list_response = client.get("/api/storefront/products")
        assert sample_uvdtf_cup_wrap.slug not in [p["slug"] for p in list_response.json()]

    def test_delete_nonexistent_product(self, client):
        """Test deleting a non-existent product."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/storefront/products/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_product_invalid_uuid(self, client):
        """Test deleting with invalid UUID."""
        response = client.delete("/api/storefront/products/invalid-uuid")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestProductResponseModel:
    """Tests for product response model structure."""

    def test_product_list_response_structure(self, client, sample_uvdtf_cup_wrap):
        """Test that product list response has correct structure."""
        response = client.get("/api/storefront/products")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()[0]

        # Required fields
        assert "id" in data
        assert "name" in data
        assert "slug" in data
        assert "price" in data
        assert "print_method" in data
        assert "category" in data
        assert "product_type" in data
        assert "is_featured" in data

        # Optional fields
        assert "short_description" in data
        assert "compare_at_price" in data
        assert "featured_image" in data

    def test_product_detail_response_structure(self, client, sample_uvdtf_cup_wrap):
        """Test that product detail response has correct structure."""
        response = client.get(f"/api/storefront/products/{sample_uvdtf_cup_wrap.slug}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Basic fields
        assert "id" in data
        assert "name" in data
        assert "slug" in data
        assert "description" in data
        assert "price" in data

        # Classification fields
        assert "product_type" in data
        assert "print_method" in data
        assert "category" in data

        # Additional fields
        assert "images" in data
        assert "has_variants" in data
        assert "variants" in data
        assert "inventory_quantity" in data
        assert "track_inventory" in data
        assert "meta_title" in data
        assert "meta_description" in data

    def test_variant_response_structure(self, client, sample_uvdtf_cup_wrap, sample_product_variants):
        """Test that variant response has correct structure."""
        response = client.get(f"/api/storefront/products/{sample_uvdtf_cup_wrap.slug}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["variants"]) > 0

        variant = data["variants"][0]
        assert "id" in variant
        assert "name" in variant
        assert "sku" in variant
        assert "price" in variant
        assert "inventory_quantity" in variant
        assert "is_active" in variant
