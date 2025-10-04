"""
Shopify Engine - Extended API client for metadata and template operations

This module extends the base ShopifyClient with additional functionality for:
- Fetching product types, vendors, tags
- Fetching theme templates
- Country of origin and HS code management
- Product variant operations with nested structure support
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from server.src.utils.shopify_client import ShopifyClient, ShopifyAPIError

logger = logging.getLogger(__name__)

class ShopifyEngine(ShopifyClient):
    """
    Extended Shopify API client with metadata fetching and template operations.
    """

    def __init__(self, db: Session, user_id: Optional[str] = None):
        """
        Initialize Shopify engine.

        Args:
            db: SQLAlchemy database session
            user_id: Optional user ID for user-specific operations
        """
        super().__init__(db)
        self.user_id = user_id

    def get_product_types(self, store_id: str, limit: int = 250) -> List[str]:
        """
        Fetch all unique product types from the store's products.

        Args:
            store_id: UUID of the store
            limit: Maximum number of products to scan

        Returns:
            List of unique product types
        """
        try:
            products = self.get_products(store_id, limit=limit, published_status="any")

            # Extract unique product types
            product_types = set()
            for product in products:
                product_type = product.get('product_type')
                if product_type and product_type.strip():
                    product_types.add(product_type.strip())

            types_list = sorted(list(product_types))
            logger.info(f"Found {len(types_list)} unique product types")
            return types_list

        except Exception as e:
            logger.error(f"Failed to fetch product types: {e}")
            raise ShopifyAPIError(f"Failed to fetch product types: {e}")

    def get_vendors(self, store_id: str, limit: int = 250) -> List[str]:
        """
        Fetch all unique vendors from the store's products.

        Args:
            store_id: UUID of the store
            limit: Maximum number of products to scan

        Returns:
            List of unique vendors
        """
        try:
            products = self.get_products(store_id, limit=limit, published_status="any")

            # Extract unique vendors
            vendors = set()
            for product in products:
                vendor = product.get('vendor')
                if vendor and vendor.strip():
                    vendors.add(vendor.strip())

            vendors_list = sorted(list(vendors))
            logger.info(f"Found {len(vendors_list)} unique vendors")
            return vendors_list

        except Exception as e:
            logger.error(f"Failed to fetch vendors: {e}")
            raise ShopifyAPIError(f"Failed to fetch vendors: {e}")

    def get_tags(self, store_id: str, limit: int = 250) -> List[str]:
        """
        Fetch all unique tags from the store's products.

        Args:
            store_id: UUID of the store
            limit: Maximum number of products to scan

        Returns:
            List of unique tags
        """
        try:
            products = self.get_products(store_id, limit=limit, published_status="any")

            # Extract unique tags
            all_tags = set()
            for product in products:
                tags = product.get('tags', '')
                if tags:
                    # Tags are comma-separated
                    tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                    all_tags.update(tag_list)

            tags_list = sorted(list(all_tags))
            logger.info(f"Found {len(tags_list)} unique tags")
            return tags_list

        except Exception as e:
            logger.error(f"Failed to fetch tags: {e}")
            raise ShopifyAPIError(f"Failed to fetch tags: {e}")

    def get_themes(self, store_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all themes from the store.

        Args:
            store_id: UUID of the store

        Returns:
            List of theme dictionaries with id, name, and role
        """
        store = self._get_store_info(store_id)
        url = f"https://{store.shop_domain}/admin/api/{self.API_VERSION}/themes.json"

        headers = self._get_headers(str(store.access_token))

        try:
            response = self._make_request_with_retry('GET', url, headers)
            data = response.json()

            themes = data.get('themes', [])
            logger.info(f"Successfully fetched {len(themes)} themes from store {store.shop_name}")

            # Return simplified theme info
            return [
                {
                    'id': theme.get('id'),
                    'name': theme.get('name'),
                    'role': theme.get('role'),  # 'main', 'unpublished', 'development'
                    'theme_store_id': theme.get('theme_store_id')
                }
                for theme in themes
            ]

        except Exception as e:
            logger.error(f"Failed to fetch themes from store {store_id}: {e}")
            raise ShopifyAPIError(f"Failed to fetch themes: {e}")

    def get_theme_templates(self, store_id: str, theme_id: Optional[str] = None) -> List[str]:
        """
        Fetch available product templates from a theme.

        Args:
            store_id: UUID of the store
            theme_id: Optional theme ID (uses main theme if not provided)

        Returns:
            List of template suffixes
        """
        try:
            # Get theme ID if not provided
            if not theme_id:
                themes = self.get_themes(store_id)
                main_theme = next((t for t in themes if t['role'] == 'main'), None)
                if not main_theme:
                    logger.warning("No main theme found")
                    return []
                theme_id = str(main_theme['id'])

            store = self._get_store_info(store_id)
            url = f"https://{store.shop_domain}/admin/api/{self.API_VERSION}/themes/{theme_id}/assets.json"

            headers = self._get_headers(str(store.access_token))

            response = self._make_request_with_retry('GET', url, headers)
            data = response.json()

            assets = data.get('assets', [])

            # Filter for product template files
            templates = []
            for asset in assets:
                key = asset.get('key', '')
                # Look for product template files (e.g., templates/product.custom.json)
                if key.startswith('templates/product.') and key.endswith('.json'):
                    # Extract template suffix (e.g., 'custom' from 'templates/product.custom.json')
                    suffix = key.replace('templates/product.', '').replace('.json', '')
                    if suffix != 'product':  # Exclude the default template
                        templates.append(suffix)

            logger.info(f"Found {len(templates)} product templates in theme {theme_id}")
            return sorted(templates)

        except Exception as e:
            logger.error(f"Failed to fetch theme templates: {e}")
            # Return empty list instead of raising to allow graceful degradation
            return []

    def get_countries_and_hs_codes(self, store_id: str) -> Dict[str, List[str]]:
        """
        Fetch available countries of origin.
        Note: HS codes are product-specific and should be entered manually or
        fetched from existing products.

        Args:
            store_id: UUID of the store

        Returns:
            Dictionary with countries list and sample HS codes from existing products
        """
        try:
            # Standard ISO country codes commonly used for e-commerce
            countries = [
                "US", "CA", "MX",  # North America
                "GB", "FR", "DE", "IT", "ES", "NL", "BE", "SE", "DK", "NO", "FI", "IE", "PT", "AT", "CH",  # Europe
                "CN", "JP", "KR", "IN", "TH", "VN", "ID", "PH", "MY", "SG", "TW", "HK",  # Asia
                "AU", "NZ",  # Oceania
                "BR", "AR", "CL", "CO", "PE",  # South America
                "ZA", "EG", "NG", "KE"  # Africa
            ]

            # Try to fetch HS codes from existing products
            hs_codes = set()
            try:
                products = self.get_products(store_id, limit=100, published_status="any")

                for product in products:
                    variants = product.get('variants', [])
                    for variant in variants:
                        hs_code = variant.get('harmonized_system_code')
                        if hs_code:
                            hs_codes.add(hs_code)
            except Exception as e:
                logger.warning(f"Could not fetch HS codes from products: {e}")

            return {
                'countries': sorted(countries),
                'hs_codes': sorted(list(hs_codes))
            }

        except Exception as e:
            logger.error(f"Failed to fetch countries and HS codes: {e}")
            raise ShopifyAPIError(f"Failed to fetch countries and HS codes: {e}")

    def create_product_with_variants(self, store_id: str, template_data: Dict[str, Any],
                                     variant_structure: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a product with complex nested variant structure.

        Args:
            store_id: UUID of the store
            template_data: Base product template data
            variant_structure: List of variant definitions with nested options
                Example:
                [
                    {
                        "parent_option": "Pack",
                        "option_name": "5 Pack",
                        "price": "25.00",
                        "weight": 500,
                        "weight_unit": "g",
                        "sku": "PROD-5PACK",
                        "inventory_quantity": 100
                    }
                ]

        Returns:
            Created product dictionary
        """
        try:
            # Build product data structure
            product_data = {
                'title': template_data.get('template_title'),
                'body_html': template_data.get('description'),
                'vendor': template_data.get('vendor'),
                'product_type': template_data.get('product_type'),
                'tags': template_data.get('tags', ''),
                'status': template_data.get('status', 'draft'),
                'published_scope': template_data.get('published_scope', 'web'),
            }

            # Add SEO metadata
            if template_data.get('seo_title') or template_data.get('seo_description'):
                product_data['metafields_global_title_tag'] = template_data.get('seo_title')
                product_data['metafields_global_description_tag'] = template_data.get('seo_description')

            # Build variants from structure
            variants = []
            for var_struct in variant_structure:
                variant = {
                    'price': str(var_struct.get('price', template_data.get('price', '0.00'))),
                    'sku': var_struct.get('sku', template_data.get('sku_prefix', '')),
                    'inventory_quantity': var_struct.get('inventory_quantity', template_data.get('inventory_quantity', 0)),
                    'inventory_management': 'shopify' if template_data.get('track_inventory', True) else None,
                    'inventory_policy': template_data.get('inventory_policy', 'deny'),
                    'fulfillment_service': template_data.get('fulfillment_service', 'manual'),
                    'requires_shipping': template_data.get('requires_shipping', True),
                    'taxable': template_data.get('is_taxable', True),
                    'weight': var_struct.get('weight', template_data.get('weight')),
                    'weight_unit': var_struct.get('weight_unit', template_data.get('weight_unit', 'g')),
                }

                # Add variant options (Shopify supports up to 3 options)
                if var_struct.get('option1'):
                    variant['option1'] = var_struct['option1']
                if var_struct.get('option2'):
                    variant['option2'] = var_struct['option2']
                if var_struct.get('option3'):
                    variant['option3'] = var_struct['option3']

                # Add country of origin and HS code if provided
                if var_struct.get('country_code_of_origin'):
                    variant['country_code_of_origin'] = var_struct['country_code_of_origin']
                if var_struct.get('harmonized_system_code'):
                    variant['harmonized_system_code'] = var_struct['harmonized_system_code']

                # Add compare at price if provided
                if var_struct.get('compare_at_price'):
                    variant['compare_at_price'] = str(var_struct['compare_at_price'])

                variants.append(variant)

            product_data['variants'] = variants

            # Add product options if variants have options
            if variant_structure and variant_structure[0].get('option1'):
                options = []
                if variant_structure[0].get('option1'):
                    options.append({
                        'name': template_data.get('option1_name', 'Option 1'),
                        'values': list(set(v.get('option1') for v in variant_structure if v.get('option1')))
                    })
                if variant_structure[0].get('option2'):
                    options.append({
                        'name': template_data.get('option2_name', 'Option 2'),
                        'values': list(set(v.get('option2') for v in variant_structure if v.get('option2')))
                    })
                if variant_structure[0].get('option3'):
                    options.append({
                        'name': template_data.get('option3_name', 'Option 3'),
                        'values': list(set(v.get('option3') for v in variant_structure if v.get('option3')))
                    })
                product_data['options'] = options

            # Create the product
            return self.create_product(store_id, product_data)

        except Exception as e:
            logger.error(f"Failed to create product with variants: {e}")
            raise ShopifyAPIError(f"Failed to create product with variants: {e}")

    def get_product_metafields(self, store_id: str, product_id: str) -> List[Dict[str, Any]]:
        """
        Get metafields for a product (for custom data storage).

        Args:
            store_id: UUID of the store
            product_id: Shopify product ID

        Returns:
            List of metafield dictionaries
        """
        store = self._get_store_info(store_id)
        url = f"https://{store.shop_domain}/admin/api/{self.API_VERSION}/products/{product_id}/metafields.json"

        headers = self._get_headers(str(store.access_token))

        try:
            response = self._make_request_with_retry('GET', url, headers)
            data = response.json()

            metafields = data.get('metafields', [])
            logger.info(f"Successfully fetched {len(metafields)} metafields for product {product_id}")
            return metafields

        except Exception as e:
            logger.error(f"Failed to fetch metafields for product {product_id}: {e}")
            raise ShopifyAPIError(f"Failed to fetch metafields: {e}")
