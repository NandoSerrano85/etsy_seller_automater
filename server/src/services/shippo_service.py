"""
Shippo API integration for real-time shipping rates.

Provides functionality to:
- Get shipping rates from multiple carriers
- Create shipping labels
- Track shipments

Documentation: https://goshippo.com/docs/
"""

import os
import logging
from typing import List, Dict, Optional, Any
import requests

logger = logging.getLogger(__name__)


def get_storefront_shipping_settings():
    """
    Get shipping settings from StorefrontSettings database.

    Returns the first user's storefront settings if available, None otherwise.
    This allows the Shippo service to use database-configured settings instead of environment variables.
    """
    try:
        from server.src.database.core import SessionLocal
        from server.src.entities.ecommerce.storefront_settings import StorefrontSettings

        db = SessionLocal()
        try:
            settings = db.query(StorefrontSettings).first()
            return settings
        finally:
            db.close()
    except Exception as e:
        logger.debug(f"Could not fetch storefront settings from database: {e}")
        return None


class ShippoService:
    """Service for interacting with Shippo API."""

    def __init__(self):
        """Initialize Shippo service with API credentials from database or environment."""
        # Try to get settings from database first
        db_settings = get_storefront_shipping_settings()

        if db_settings and db_settings.shippo_api_key:
            # Use database settings
            self.api_key = db_settings.shippo_api_key
            self.test_mode = db_settings.shippo_test_mode.lower() == 'true' if db_settings.shippo_test_mode else True
            logger.info("Using Shippo settings from database")
        else:
            # Fall back to environment variables
            self.api_key = os.getenv('SHIPPO_API_KEY')
            self.test_mode = os.getenv('SHIPPO_TEST_MODE', 'true').lower() == 'true'
            logger.info("Using Shippo settings from environment variables")

        self.api_url = 'https://api.goshippo.com'

        if not self.api_key:
            logger.warning("SHIPPO_API_KEY not configured. Shipping rate calculation will use fallback values.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Shippo service initialized (test_mode: {self.test_mode})")

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make authenticated request to Shippo API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request payload

        Returns:
            API response as dictionary
        """
        url = f"{self.api_url}{endpoint}"
        headers = {
            'Authorization': f'ShippoToken {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.request(method, url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Shippo API request failed: {e}")
            raise

    def get_shipping_rates(
        self,
        to_address: Dict[str, str],
        from_address: Optional[Dict[str, str]] = None,
        parcel: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Get real-time shipping rates from multiple carriers.

        Args:
            to_address: Destination address
                {
                    'name': 'Customer Name',
                    'street1': '123 Main St',
                    'street2': 'Apt 4',  # optional
                    'city': 'San Francisco',
                    'state': 'CA',
                    'zip': '94105',
                    'country': 'US',
                    'phone': '555-1234',  # optional
                    'email': 'customer@example.com'  # optional
                }
            from_address: Origin address (uses default if not provided)
            parcel: Package dimensions
                {
                    'length': '5',  # inches
                    'width': '5',
                    'height': '5',
                    'distance_unit': 'in',
                    'weight': '2',  # pounds
                    'mass_unit': 'lb'
                }

        Returns:
            List of shipping rates with carrier, service, and price
        """
        if not self.enabled:
            logger.warning("Shippo not configured, returning fallback rates")
            return self._get_fallback_rates()

        try:
            # Use default origin address if not provided
            if not from_address:
                from_address = self._get_default_origin_address()

            # Use default parcel if not provided
            if not parcel:
                parcel = self._get_default_parcel()

            # Create shipment to get rates
            shipment_data = {
                'address_from': from_address,
                'address_to': to_address,
                'parcels': [parcel],
                'async': False  # Get rates synchronously
            }

            logger.info(f"Requesting shipping rates from {from_address.get('city', 'unknown')} to {to_address.get('city', 'unknown')}")

            response = self._make_request('POST', '/shipments/', shipment_data)

            # Extract rates from response
            rates = []
            if 'rates' in response:
                for rate in response['rates']:
                    rates.append({
                        'carrier': rate.get('provider', 'Unknown'),
                        'service': rate.get('servicelevel', {}).get('name', 'Standard'),
                        'service_level': rate.get('servicelevel', {}).get('token', ''),
                        'amount': float(rate.get('amount', 0)),
                        'currency': rate.get('currency', 'USD'),
                        'estimated_days': rate.get('estimated_days', None),
                        'duration_terms': rate.get('duration_terms', ''),
                        'rate_id': rate.get('object_id', ''),
                        'shippo_rate': rate  # Store full rate object for label creation
                    })

            # Sort by price (cheapest first)
            rates.sort(key=lambda x: x['amount'])

            logger.info(f"Retrieved {len(rates)} shipping rates")
            return rates

        except Exception as e:
            logger.error(f"Failed to get shipping rates: {e}")
            return self._get_fallback_rates()

    def _get_default_origin_address(self) -> Dict[str, str]:
        """
        Get default origin/warehouse address from database or environment.

        Returns:
            Origin address dictionary
        """
        # Try to get from database first
        db_settings = get_storefront_shipping_settings()

        if db_settings and db_settings.shipping_from_street1:
            # Use database settings
            return {
                'name': db_settings.shipping_from_name or 'CraftFlow Commerce',
                'company': db_settings.shipping_from_company or 'CraftFlow Commerce',
                'street1': db_settings.shipping_from_street1,
                'street2': db_settings.shipping_from_street2 or '',
                'city': db_settings.shipping_from_city or 'Miami',
                'state': db_settings.shipping_from_state or 'FL',
                'zip': db_settings.shipping_from_zip or '33101',
                'country': db_settings.shipping_from_country or 'US',
                'phone': db_settings.shipping_from_phone or '555-0100',
                'email': db_settings.shipping_from_email or 'shipping@craftflow.com'
            }

        # Fall back to environment variables
        return {
            'name': os.getenv('SHIPPO_FROM_NAME', 'CraftFlow Commerce'),
            'company': os.getenv('SHIPPO_FROM_COMPANY', 'CraftFlow Commerce'),
            'street1': os.getenv('SHIPPO_FROM_STREET1', '123 Business St'),
            'street2': os.getenv('SHIPPO_FROM_STREET2', ''),
            'city': os.getenv('SHIPPO_FROM_CITY', 'Miami'),
            'state': os.getenv('SHIPPO_FROM_STATE', 'FL'),
            'zip': os.getenv('SHIPPO_FROM_ZIP', '33101'),
            'country': os.getenv('SHIPPO_FROM_COUNTRY', 'US'),
            'phone': os.getenv('SHIPPO_FROM_PHONE', '555-0100'),
            'email': os.getenv('SHIPPO_FROM_EMAIL', 'shipping@craftflow.com')
        }

    def _get_default_parcel(self) -> Dict[str, Any]:
        """
        Get default parcel dimensions from database or environment.

        Returns:
            Parcel specifications dictionary
        """
        # Try to get from database first
        db_settings = get_storefront_shipping_settings()

        if db_settings and db_settings.shipping_default_length:
            # Use database settings
            return {
                'length': db_settings.shipping_default_length or '10',
                'width': db_settings.shipping_default_width or '8',
                'height': db_settings.shipping_default_height or '4',
                'distance_unit': 'in',
                'weight': db_settings.shipping_default_weight or '1',
                'mass_unit': 'lb'
            }

        # Fall back to environment variables
        return {
            'length': os.getenv('SHIPPO_DEFAULT_LENGTH', '10'),
            'width': os.getenv('SHIPPO_DEFAULT_WIDTH', '8'),
            'height': os.getenv('SHIPPO_DEFAULT_HEIGHT', '4'),
            'distance_unit': 'in',
            'weight': os.getenv('SHIPPO_DEFAULT_WEIGHT', '1'),
            'mass_unit': 'lb'
        }

    def _get_fallback_rates(self) -> List[Dict]:
        """
        Get fallback shipping rates when Shippo is not available.

        Returns:
            List of basic shipping options
        """
        return [
            {
                'carrier': 'USPS',
                'service': 'First Class Package',
                'service_level': 'usps_first',
                'amount': 5.99,
                'currency': 'USD',
                'estimated_days': 3,
                'duration_terms': '2-5 business days',
                'rate_id': 'fallback_first_class',
                'is_fallback': True
            },
            {
                'carrier': 'USPS',
                'service': 'Priority Mail',
                'service_level': 'usps_priority',
                'amount': 9.99,
                'currency': 'USD',
                'estimated_days': 2,
                'duration_terms': '1-3 business days',
                'rate_id': 'fallback_priority',
                'is_fallback': True
            },
            {
                'carrier': 'USPS',
                'service': 'Priority Mail Express',
                'service_level': 'usps_express',
                'amount': 24.99,
                'currency': 'USD',
                'estimated_days': 1,
                'duration_terms': 'Overnight',
                'rate_id': 'fallback_express',
                'is_fallback': True
            }
        ]

    def create_shipping_label(
        self,
        rate_id: str,
        label_file_type: str = 'PDF'
    ) -> Dict:
        """
        Create a shipping label from a rate.

        Args:
            rate_id: Shippo rate object ID
            label_file_type: Label format (PDF, PNG, etc.)

        Returns:
            Transaction object with label URL
        """
        if not self.enabled:
            raise ValueError("Shippo not configured")

        try:
            transaction_data = {
                'rate': rate_id,
                'label_file_type': label_file_type,
                'async': False
            }

            response = self._make_request('POST', '/transactions/', transaction_data)

            logger.info(f"Created shipping label: {response.get('object_id')}")

            return {
                'transaction_id': response.get('object_id'),
                'tracking_number': response.get('tracking_number'),
                'tracking_url': response.get('tracking_url_provider'),
                'label_url': response.get('label_url'),
                'carrier': response.get('rate', {}).get('provider'),
                'service': response.get('rate', {}).get('servicelevel', {}).get('name'),
                'status': response.get('status')
            }

        except Exception as e:
            logger.error(f"Failed to create shipping label: {e}")
            raise

    def track_shipment(self, carrier: str, tracking_number: str) -> Dict:
        """
        Track a shipment by tracking number.

        Args:
            carrier: Carrier name (usps, ups, fedex, etc.)
            tracking_number: Tracking number

        Returns:
            Tracking information
        """
        if not self.enabled:
            raise ValueError("Shippo not configured")

        try:
            endpoint = f'/tracks/{carrier}/{tracking_number}'
            response = self._make_request('GET', endpoint)

            return {
                'carrier': response.get('carrier'),
                'tracking_number': response.get('tracking_number'),
                'status': response.get('tracking_status', {}).get('status'),
                'status_details': response.get('tracking_status', {}).get('status_details'),
                'eta': response.get('eta'),
                'tracking_history': response.get('tracking_history', [])
            }

        except Exception as e:
            logger.error(f"Failed to track shipment: {e}")
            raise


# Global instance
shippo_service = ShippoService()
