import requests, os,  hashlib, base64, secrets, time, re, logging
from typing import List, Dict, Optional
from urllib.parse import urlencode
from collections import deque
from server.src.entities.third_party_oauth import ThirdPartyOAuthToken
from server.src.utils.nas_storage import nas_storage

class EtsyAPI:
    def __init__(self, user_id=None, db=None):
        """
        Initialize the Etsy listing uploader with OAuth credentials
        Args:
            user_id (UUID): The user ID to fetch OAuth credentials for
            db (Session): SQLAlchemy DB session
        """
        self.session = requests.Session()
        # Configure SSL handling for Etsy API
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.base_url = "https://openapi.etsy.com/v3"
        self.ping_url = "https://api.etsy.com/v3/application/openapi-ping"
        self.access_token = None
        self.user_id = user_id
        self.db = db
        # Try to load tokens from DB if user_id and db are provided
        self.oauth_token = None
        self.refresh_token = None
        self.token_expiry = 0
        if user_id and db:
            token_obj = db.query(ThirdPartyOAuthToken).filter(ThirdPartyOAuthToken.user_id == user_id).first()
            if token_obj:
                self.oauth_token = token_obj.access_token
                self.refresh_token = token_obj.refresh_token
                self.token_expiry = token_obj.expires_at.timestamp() if token_obj.expires_at else 0
                logging.info(f"Loaded Etsy tokens from database for user {user_id}")
            else:
                logging.warning(f"No Etsy tokens found in database for user {user_id}. User needs to connect their Etsy account.")
        else:
            logging.error("Cannot load Etsy tokens: user_id or database session not provided")
        # Only proceed if we have valid tokens
        if self.oauth_token:
            # Authenticate with correct scopes if needed
            self.authenticate_with_scopes()
            # Get shop ID from environment or fetch it automatically
            self.shop_id = self.fetch_user_shop_id()
            if self.shop_id:
                print(f"Using shop ID: {self.shop_id}")
            else:
                raise Exception("Could not fetch shop ID from Etsy API. Please reconnect your Etsy account in the application settings.")
        else:
            logging.warning("No Etsy access token available. API operations will not be possible until user connects their Etsy account.")
            self.shop_id = None
            self.taxonomy_id = None
            self.shipping_profile_id = None
            self.shop_section_id = None
            self.readiness_state_id = None

        # Only fetch additional data if we have valid tokens and shop_id
        if self.oauth_token and self.shop_id:
            self.taxonomy_id = self.fetch_taxonomies()
            self.shipping_profile_id = self.fetch_shipping_profiles()
            self.shop_section_id = self.fetch_shop_sections()
            self.readiness_state_id = self.fetch_shop_readiness_state_id()
        else:
            self.taxonomy_id = None
            self.shipping_profile_id = None
            self.shop_section_id = None
            self.readiness_state_id = None

    def is_authenticated(self) -> bool:
        """Check if the engine has valid Etsy authentication"""
        return bool(self.oauth_token and self.shop_id)

    def require_authentication(self):
        """Raise an exception if not authenticated"""
        if not self.is_authenticated():
            raise Exception("Etsy account not connected. Please connect your Etsy account first.")

    def _find_index(self, lst, element):
        try:
            return lst.index(element)
        except ValueError:
            return -1 

    def _find_nodes_bfs(self, root, condition):
        """Find all nodes matching a condition using BFS"""
        found = []
        queue = deque([root])
        
        while queue:
            current = queue.popleft()
            
            if condition(current):
                found.append(current)
            
            if 'children' in current and current['children']:
                queue.extend(current['children'])
        
        return found
    
    def authenticate_with_scopes(self):
        """Authenticate with OAuth to get proper scopes"""
        if not self.oauth_token:
            print("No OAuth token found. Starting OAuth flow...")
            self.perform_oauth_flow()
        else:
            # Test current token and refresh if needed
            if not self.test_token():
                print("Current token invalid or missing scopes. Starting OAuth flow...")
                self.perform_oauth_flow()

    def is_token_expired(self):
        return time.time() > self.token_expiry - 60  # refresh 1 min before expiry

    def refresh_access_token(self):
        token_url = "https://api.etsy.com/v3/public/oauth/token"
        refresh_token = self.refresh_token
        if not refresh_token:
            raise Exception("No refresh token available.")

        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'refresh_token': refresh_token,
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        logging.info("Refreshing Etsy OAuth token...")
        resp = self.session.post(token_url, data=data, headers=headers)

        if resp.status_code == 200:
            token_info = resp.json()
            self.oauth_token = token_info.get('access_token')
            new_refresh_token = token_info.get('refresh_token')
            if new_refresh_token:  # Some providers don't return a new refresh token
                self.refresh_token = new_refresh_token
            expires_in = token_info.get('expires_in', 3600)
            self.token_expiry = time.time() + expires_in

            # Save refreshed tokens to database first (primary storage)
            if self.user_id and self.db:
                try:
                    from datetime import datetime, timezone
                    expires_at = datetime.fromtimestamp(self.token_expiry, tz=timezone.utc)

                    # Find existing token record
                    token_obj = self.db.query(ThirdPartyOAuthToken).filter(
                        ThirdPartyOAuthToken.user_id == self.user_id
                    ).first()

                    if token_obj:
                        # Update existing record
                        token_obj.access_token = self.oauth_token
                        if new_refresh_token:
                            token_obj.refresh_token = self.refresh_token
                        token_obj.expires_at = expires_at
                        token_obj.updated_at = datetime.now(timezone.utc)
                    else:
                        # Create new record
                        token_obj = ThirdPartyOAuthToken(
                            user_id=self.user_id,
                            provider='etsy',
                            access_token=self.oauth_token,
                            refresh_token=self.refresh_token,
                            expires_at=expires_at,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc)
                        )
                        self.db.add(token_obj)

                    self.db.commit()
                    logging.info("Successfully saved refreshed tokens to database")

                except Exception as db_error:
                    logging.error(f"Failed to save tokens to database: {db_error}")
                    self.db.rollback()
                    # Continue anyway - token refresh succeeded

            # Note: Tokens are now stored only in database - .env file updating removed

            logging.info("Access token refreshed successfully")
        else:
            error_msg = f"Failed to refresh token: {resp.status_code} - {resp.text}"
            logging.error(error_msg)
            raise Exception(error_msg)

    def ensure_valid_token(self):
        if self.is_token_expired():
            logging.info("Access token expired or about to expire, refreshing...")
            try:
                self.refresh_access_token()
            except Exception as e:
                logging.error(f"Failed to refresh access token: {e}")
                # Don't raise the exception - let the API call proceed and fail with a proper HTTP error
                # This prevents the entire application from crashing
                logging.warning("Proceeding with expired token - API calls may fail with 401 errors")

    def test_token(self):
        self.ensure_valid_token()
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        }
        try:
            resp = self.session.get(f"{self.base_url}/application/openapi-ping", headers=headers)
            return resp.status_code == 200
        except:
            return False

    def perform_oauth_flow(self):
        """Perform OAuth flow to get token with correct scopes"""
        # Required scopes for Etsy API (space-separated)
        scopes = "listings_w listings_r shops_r shops_w transactions_r"
        
        # Generate PKCE code verifier and challenge
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).decode('utf-8').rstrip('=')
        
        # Step 1: Get authorization URL
        auth_url = "https://www.etsy.com/oauth/connect"
        params = {
            'response_type': 'code',
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'scope': scopes,
            'client_id': self.client_id,
            'state': secrets.token_urlsafe(32),
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        # Build URL with proper parameter encoding
        auth_url_with_params = f"{auth_url}?{urlencode(params)}"
        
        print(f"\nPlease visit this URL to authorize the application:")
        print(auth_url_with_params)
        print("\nAfter authorization, you'll get a code. Please enter it here:")
        
        authorization_code = input("Enter the authorization code: ").strip()
        
        # Step 2: Exchange code for access token
        token_url = "https://api.etsy.com/v3/public/oauth/token"
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'code': authorization_code,
            'code_verifier': code_verifier
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            resp = self.session.post(token_url, data=token_data, headers=headers)
            if resp.status_code == 200:
                token_info = resp.json()
                self.oauth_token = token_info.get('access_token')
                self.refresh_token = token_info.get('refresh_token')
                print("OAuth authentication successful!")
                print(f"Please update your .env file with: ETSY_OAUTH_TOKEN={self.oauth_token}")
            else:
                print(f"Failed to get access token: {resp.text}")
                raise Exception("OAuth authentication failed")
        except Exception as e:
            print(f"Error during OAuth flow: {e}")
            raise Exception("OAuth authentication failed")

    def get_shop_details(self) -> Optional[dict]:
        """
        Get shop details including icon URL

        Returns:
            dict: Shop details including icon_url_fullxfull
        """
        if not self.shop_id:
            logging.error("No shop ID available")
            return None

        self.ensure_valid_token()
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
        }

        url = f"{self.base_url}/application/shops/{self.shop_id}"

        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to fetch shop details: {e}")
            return None

    def get_receipt_shipment(self, receipt_id: int) -> Optional[dict]:
        """
        Get shipment details for a receipt including shipping address

        Args:
            receipt_id: The receipt ID

        Returns:
            dict: Shipment details with shipping address
        """
        if not self.shop_id:
            logging.error("No shop ID available")
            return None

        self.ensure_valid_token()
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
        }

        url = f"{self.base_url}/application/shops/{self.shop_id}/receipts/{receipt_id}/shipments"

        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            shipments = response.json().get('results', [])
            if shipments:
                return shipments[0]  # Return first shipment
            return None
        except Exception as e:
            logging.error(f"Failed to fetch shipment for receipt {receipt_id}: {e}")
            return None

    def fetch_user_shop_id(self) -> Optional[int]:
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
        }
        # Fetch the shop ID that the access token is authorized for
        # instead of using a hardcoded SHOP_ID
        user_url = f"{self.base_url}/application/users/me"
        user_response = self.session.get(user_url, headers=headers)
        if not user_response.ok:
            logging.error(f"Failed to fetch user data: {user_response.status_code} {user_response.text}")
            return None
        
        user_data = user_response.json()
        user_id = user_data.get('user_id')
        
        if not user_id:
            logging.error("Could not get user ID from access token")
            return None
        
        # Fetch shops owned by this user
        shops_url = f"{self.base_url}/application/users/{user_id}/shops"
        shops_response = self.session.get(shops_url, headers=headers)
        if not shops_response.ok:
            logging.error(f"Failed to fetch user shops: {shops_response.status_code} {shops_response.text}")
            return None
        
        shops_data = shops_response.json()
        
        # Handle different response formats from Etsy API
        if not shops_data:
            logging.error("No shops data received from Etsy API")
            return None
        
        # Check if response has 'results' array (standard format)
        if 'results' in shops_data and shops_data['results']:
            first_shop = shops_data['results'][0]
        # Check if response is a direct shop object
        elif 'shop_id' in shops_data:
            first_shop = shops_data
        else:
            logging.error(f"Unexpected shop data format: {shops_data}")
            return None
        
        shop_id = first_shop.get('shop_id')
        
        if not shop_id:
            logging.error(f"Shop ID not found in shop data: {first_shop}")
            return None
            
        return shop_id

    def fetch_shop_readiness_state_id(self) -> Optional[int]:
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
        }

        readiness_url = f"{self.base_url}/application/shops/{self.shop_id}/readiness-state-definitions"

        readines_response = self.session.get(readiness_url, headers=headers)

        if not readines_response.ok:
            logging.error(f"Failed to fetch shop readiness state: {readines_response.status_code} {readines_response.text}")
            return None
        
        readiness_data = readines_response.json()
        readiness_state_id = readiness_data['results'][0].get('readiness_state_id')
        if not readiness_state_id:
            logging.error(f"Readiness state ID not found in response: {readiness_data}")
            return None

        return readiness_state_id

    def create_draft_listing(self, title: str, description: str, price: float,
                           quantity: int, tags: List[str],
                           materials: List[str],
                           item_weight: float,
                           item_weight_unit: str,
                           item_dimensions_unit: str,
                           item_length: float,
                           item_width: float,
                           item_height: float,
                           return_policy_id: Optional[int] = None,
                           is_digital: bool = False,
                           when_made: str = "made_to_order",
                           production_partner_ids: Optional[List[int]] = None,
                           ) -> Dict:
        """
        Create a draft listing on Etsy

        Args:
            title (str): Product title
            description (str): Product description
            price (float): Product price
            quantity (int): Available quantity
            tags (List[str]): Product tags
            materials (List[str]): Product materials
            taxonomy_id (int): Etsy taxonomy ID for the product
            shipping_profile_id (int): Shipping profile ID
            return_policy_id (int): Return policy ID
            is_digital (bool): Whether this is a digital product
            production_partner_ids (List[int]): Production partner IDs (required for physical listings)
        Returns:
            Dict: Response from Etsy API containing listing ID
        """
        endpoint = f"{self.base_url}/application/shops/{self.shop_id}/listings"
        payload = {
            "quantity": quantity,
            "title": title,
            "description": description,
            "price": price,
            "who_made": "i_did",
            "when_made": when_made,
            "item_weight": item_weight,
            "item_weight_unit": item_weight_unit,
            "item_length": item_length,
            "item_width": item_width,
            "item_height": item_height,
            "item_dimensions_unit": item_dimensions_unit,
            "taxonomy_id": self.taxonomy_id if self.taxonomy_id else 1071,
            "tags": tags[:13],  # Etsy allows max 13 tags
            "materials": materials[:13],  # Etsy allows max 13 materials
            "shop_section_id": self.shop_section_id if self.shop_section_id else 52993337,
            "shipping_profile_id": self.shipping_profile_id if self.shipping_profile_id else 1,
            "state": "draft",
            "return_policy_id": return_policy_id if return_policy_id else 1,
            "type": "physical" if not is_digital else "download",
        }

        # For physical listings, production_partner_ids and readiness_state_id are required
        # This indicates "ready to ship" status
        if not is_digital:
            if production_partner_ids:
                payload["production_partner_ids"] = production_partner_ids
            else:
                # Default to empty array which means "ready to ship" (made by seller)
                payload["production_partner_ids"] = []

            # Ensure readiness_state_id is set for physical listings (REQUIRED by Etsy)
            # If not already set, use 1 (the default "Ready to ship" state)
            if not self.readiness_state_id:
                logging.warning("readiness_state_id not set, using default value of 1 (Ready to ship)")
                payload["readiness_state_id"] = 1
            else:
                payload["readiness_state_id"] = self.readiness_state_id
        else:
            # For digital listings, readiness_state_id is optional
            if self.readiness_state_id:
                payload["readiness_state_id"] = self.readiness_state_id

        # Only include return_policy_id if it's valid (>= 1)
        if return_policy_id and return_policy_id >= 1:
            payload["return_policy_id"] = return_policy_id
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
            'Content-Type': 'application/json'
        }
        response = self.session.post(endpoint, headers=headers, json=payload)
        if response.status_code != 201:
            raise Exception(f"Failed to create listing: {response.text}")
        return response.json()

    def upload_listing_image(self, listing_id: int, image_path: str) -> Dict:
        """
        Upload an image to a listing (supports both local and NAS paths)

        Args:
            listing_id (int): The ID of the listing to add the image to
            image_path (str): Path to the image file (local or NAS path)
        Returns:
            Dict: Response from Etsy API
        """
        endpoint = f"{self.base_url}/application/shops/{self.shop_id}/listings/{listing_id}/images"
        headers = {
            "x-api-key": self.client_id,
            "Authorization": f"Bearer {self.oauth_token}"
        }

        # Check if running in production and path is NAS
        is_production = os.getenv('RAILWAY_ENVIRONMENT_NAME') or os.getenv('DOCKER_ENV')

        if is_production and image_path.startswith('/share/'):
            # Load from NAS
            try:
                from server.src.utils.nas_storage import nas_storage
                logging.info(f"Loading image from NAS for Etsy upload: {image_path}")

                # Extract shop_name and relative_path from full path
                # Path format: /share/Graphics/ShopName/RelativePath
                path_parts = image_path.split('/')
                if len(path_parts) >= 4 and path_parts[2] == 'Graphics':
                    shop_name = path_parts[3]
                    relative_path = '/'.join(path_parts[4:])

                    # Download file to memory
                    file_content = nas_storage.download_file_to_memory(shop_name, relative_path)
                    if file_content:
                        files = {
                            'image': (os.path.basename(image_path), file_content, 'image/jpeg')
                        }
                        response = self.session.post(endpoint, headers=headers, files=files)
                        response.raise_for_status()
                        logging.info(f"Successfully uploaded image from NAS to Etsy listing {listing_id}")
                        return response.json()
                    else:
                        raise Exception(f"Failed to download image from NAS: {image_path}")
                else:
                    raise Exception(f"Invalid NAS path format: {image_path}")
            except Exception as e:
                logging.error(f"Error loading image from NAS: {str(e)}")
                raise
        else:
            # Load from local filesystem
            with open(image_path, 'rb') as image_file:
                files = {
                    'image': (os.path.basename(image_path), image_file, 'image/jpeg')
                }
                response = self.session.post(endpoint, headers=headers, files=files)
                response.raise_for_status()
                return response.json()

    def publish_listing(self, listing_id: int) -> Dict:
        """
        Publish a draft listing
        
        Args:
            listing_id (int): The ID of the draft listing to publish
        Returns:
            Dict: Response from Etsy API
        """
        endpoint = f"{self.base_url}/application/shops/{self.shop_id}/listings/{listing_id}"
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            "state": "active"
        }
        response = self.session.patch(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def fetch_taxonomies(self, limit=100):
        self.ensure_valid_token()
        url = 'https://openapi.etsy.com/v3/application/seller-taxonomy/nodes'
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        }
        resp = self.session.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            taxonomy_id = None
            print("\n--- Taxonomies (categories) ---")
            for node in data.get('results', [])[:limit]:
                child_nodes = self._find_nodes_bfs(node, lambda n: not n.get('children'))
                for child in child_nodes:
                    if child['name'] == "Tumblers & Water Glasses":
                        taxonomy_id = child['id']
            return taxonomy_id if taxonomy_id else None
        elif resp.status_code in [401, 403]:
            print(f"Authentication error: {resp.text}")
            print("Make sure your OAuth token has the required scopes: listings_w, listings_r, shops_r, shops_w")
            return None
        else:
            print(f"Failed to fetch taxonomies: {resp.text}")
            return None

    def fetch_all_taxonomies(self, limit=5000):
        self.ensure_valid_token()
        url = 'https://openapi.etsy.com/v3/application/seller-taxonomy/nodes'
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        }
        resp = self.session.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            taxonomy_list = []
            print("\n--- Taxonomies (categories) ---")
            for node in data.get('results', [])[:limit]:
                child_nodes = self._find_nodes_bfs(node, lambda n: not n.get('children'))
                for child in child_nodes:
                    taxonomy_list.append({"id": child["id"], "name": child["name"]})
            taxonomy_list.sort(key=lambda x: x["name"].lower())
            return taxonomy_list
        elif resp.status_code in [401, 403]:
            print(f"Authentication error: {resp.text}")
            print("Make sure your OAuth token has the required scopes: listings_w, listings_r, shops_r, shops_w")
            return None
        else:
            print(f"Failed to fetch taxonomies: {resp.text}")
            return None

            
    def fetch_shipping_profiles(self):
        self.ensure_valid_token()
        url = f'https://openapi.etsy.com/v3/application/shops/{self.shop_id}/shipping-profiles'
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        }
        resp = self.session.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print("\n--- Shipping Profiles ---")
            for profile in data.get('results', []):
                print(f"ID: {profile['shipping_profile_id']}, Name: {profile['title']}")
            return data.get('results', [])[0]['shipping_profile_id'] if data.get('results') else None
        elif resp.status_code in [401, 403]:
            print(f"Authentication error: {resp.text}")
            print("Make sure your OAuth token has the 'shops_r' scope")
            return None
        else:
            print(f"Failed to fetch shipping profiles: {resp.text}")
            return None

    def fetch_all_shipping_profiles(self):
        """Fetch all shipping profiles from the Etsy API and return as a sorted list of dicts."""
        self.ensure_valid_token()
        url = f'https://openapi.etsy.com/v3/application/shops/{self.shop_id}/shipping-profiles'
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        }
        resp = self.session.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            profile_list = []
            for profile in data.get('results', []):
                profile_list.append({"id": profile["shipping_profile_id"], "name": profile["title"]})
            profile_list.sort(key=lambda x: x["name"].lower())
            return profile_list
        elif resp.status_code in [401, 403]:
            print(f"Authentication error: {resp.text}")
            print("Make sure your OAuth token has the 'shops_r' scope")
            return None
        else:
            print(f"Failed to fetch shipping profiles: {resp.text}")
            return None

    def fetch_shop_sections(self):
        self.ensure_valid_token()
        """Fetch shop sections from the Etsy API"""
        url = f'https://openapi.etsy.com/v3/application/shops/{self.shop_id}/sections'
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        }
        resp = self.session.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print("\n--- Shop Sections ---")
            for section in data.get('results', []):
                print(f"ID: {section['shop_section_id']}, Name: {section['title']}")
            return data.get('results', [])[1]['shop_section_id'] if data.get('results') else None
        elif resp.status_code in [401, 403]:
            print(f"Authentication error: {resp.text}")
            print("Make sure your OAuth token has the 'shops_r' scope")
            return None
        else:
            print(f"Failed to fetch shop sections: {resp.text}")
            return None

    def fetch_all_shop_sections(self):
        self.ensure_valid_token()
        """Fetch all shop sections from the Etsy API and return as a sorted list of dicts."""
        url = f'https://openapi.etsy.com/v3/application/shops/{self.shop_id}/sections'
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        }
        resp = self.session.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            section_list = []
            for section in data.get('results', []):
                section_list.append({"id": section["shop_section_id"], "name": section["title"]})
            section_list.sort(key=lambda x: x["name"].lower())
            return section_list
        elif resp.status_code in [401, 403]:
            print(f"Authentication error: {resp.text}")
            print("Make sure your OAuth token has the 'shops_r' scope")
            return None
        else:
            print(f"Failed to fetch shop sections: {resp.text}")
            return None

    def fetch_open_orders_items(self, image_dir, item_type):
        self.ensure_valid_token()
        """
        Fetch all open (paid, unshipped) orders and return a summary of product items and their total quantities.
        """
        print("\n--- Fetching Open Orders Items ---")
        receipts_url = f"https://openapi.etsy.com/v3/application/shops/{self.shop_id}/receipts?was_paid=true&was_shipped=false&was_canceled=false"
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        }
        resp = self.session.get(receipts_url, headers=headers)
        if resp.status_code != 200:
            print(f"Failed to fetch open orders: {resp.text} with status code {resp.status_code}")
            return None
        receipts = resp.json().get('results', [])
        item_summary = {}
        item_summary[item_type] = {'Title':[], 'Size':[], 'Total':[]}
        item_summary["Total QTY"] = 0
        for receipt in receipts:
            receipt_id = receipt['receipt_id']
            transactions_url = f"https://openapi.etsy.com/v3/application/shops/{self.shop_id}/receipts/{receipt_id}/transactions"
            t_resp = self.session.get(transactions_url, headers=headers)
            if t_resp.status_code != 200:
                print(f"Failed to fetch transactions for receipt {receipt_id}: {t_resp.text} with status code {t_resp.status_code}")
                continue
            transactions = t_resp.json().get('results', [])
            for t in transactions:
                title = t.get('title', 'Unknown')
                quantity = t.get('quantity', 0)
                key = self.find_images_by_name(title.split(" | ")[0], f"{image_dir}{item_type}/")
                i = self._find_index(item_summary[item_type]['Title'], key)
                if i >= 0:
                    item_summary[item_type]['Total'][i] += quantity
                else:
                    item_summary[item_type]['Title'].append(key)
                    item_summary[item_type]['Size'].append("")
                    item_summary[item_type]['Total'].append(quantity)
                item_summary["Total QTY"] += quantity
        print("\nOpen Orders Item Summary:")
        for k,v in item_summary[item_type].items():
            print(f"{k}: {v}")
        return item_summary

    def find_images_by_name(self, search_name, image_dir, extensions=(".png")):
        """
        Search for image files in image_dir (recursively) whose filenames match search_name (regex).
        Returns a list of full paths to all matches.
        """
        parts = search_name.split(" ")
        search_name = " ".join(parts[:2])
        pattern = re.compile(re.escape(search_name), re.IGNORECASE)
        for root, _, files in os.walk(image_dir):
            for file in files:
                if file.lower().endswith(extensions) and pattern.search(file):
                    full_path = os.path.join(root, file)
                    return full_path

    def find_images_by_name_nas(self, search_name, shop_name, template_name, extensions=(".png", ".jpg", ".jpeg")):
        """
        Search for design files on NAS that match search_name.
        Returns the relative path if found, None if not found.

        Args:
            search_name: Name to search for in filenames
            shop_name: Shop name for NAS path
            template_name: Template name for NAS directory
            extensions: File extensions to search for
        """
        logging.info(f"🔍 NAS Search called with: search_name='{search_name}', shop_name='{shop_name}', template='{template_name}'")

        if not nas_storage.enabled:
            logging.error("❌ NAS storage NOT enabled! Cannot search for images")
            return None

        logging.info(f"✅ NAS storage is enabled")

        # Normalize whitespace - replace multiple spaces with single space and trim
        import re as regex_module
        normalized_search = regex_module.sub(r'\s+', ' ', search_name.strip())

        parts = normalized_search.split(" ")
        search_name = " ".join(parts[:2])

        # Create multiple patterns to try different matching approaches
        patterns = []

        logging.info(f"Creating search patterns for: '{search_name}' (normalized from: '{normalized_search}', parts: {parts})")

        # Pattern 1: Exact match
        patterns.append(re.compile(re.escape(search_name), re.IGNORECASE))

        # Pattern 2: Without spaces
        no_space = search_name.replace(" ", "")
        if no_space != search_name:
            patterns.append(re.compile(re.escape(no_space), re.IGNORECASE))

        # Pattern 3: With underscores instead of spaces
        with_underscores = search_name.replace(" ", "_")
        if with_underscores != search_name:
            patterns.append(re.compile(re.escape(with_underscores), re.IGNORECASE))

        # Pattern 4: With hyphens instead of spaces
        with_hyphens = search_name.replace(" ", "-")
        if with_hyphens != search_name:
            patterns.append(re.compile(re.escape(with_hyphens), re.IGNORECASE))

        # Pattern 5: Just the number part (for patterns like "UV 674" -> "674")
        # This handles filenames like "Cup_Wrap_402.png" or "UVDTF_16oz_404.png"
        if len(parts) > 1 and parts[1].isdigit():
            number = parts[1]
            # Match number with word boundaries or underscores (e.g., "_402" or "402.")
            patterns.append(re.compile(rf'[_\s-]{re.escape(number)}(?:\.|$)', re.IGNORECASE))
            # Also match just the number anywhere
            patterns.append(re.compile(re.escape(number), re.IGNORECASE))
            # Also try with leading zeros
            padded_number = parts[1].zfill(3)  # e.g., "674" -> "674", "74" -> "074"
            if padded_number != parts[1]:
                patterns.append(re.compile(rf'[_\s-]{re.escape(padded_number)}(?:\.|$)', re.IGNORECASE))
                patterns.append(re.compile(re.escape(padded_number), re.IGNORECASE))

        # Pattern 6: More flexible matching - allow word boundaries
        # This helps match "UV604" in filename when searching for "UV 604"
        flexible_pattern = search_name.replace(" ", r"[\s_-]*")
        patterns.append(re.compile(flexible_pattern, re.IGNORECASE))

        # Pattern 7: Strip all whitespace and match at start of filename (without extension)
        # This handles cases where filename is "UV 632.png" and we're searching for "UV 632"
        stripped_search = search_name.replace(" ", r"\s*")
        patterns.append(re.compile(rf"^{stripped_search}(?:\\.|\s|$)", re.IGNORECASE))

        logging.info(f"Created {len(patterns)} search patterns for '{search_name}'")

        # List files in the template directory on NAS
        template_relative_path = template_name  # Remove trailing slash - might cause issues
        try:
            logging.info(f"📂 About to call nas_storage.list_files('{shop_name}', '{template_relative_path}')")
            files = nas_storage.list_files(shop_name, template_relative_path)
            logging.info(f"📂 nas_storage.list_files returned: {type(files)}, length: {len(files) if files else 0}")

            if files:
                filenames = [f.get('filename', '') if isinstance(f, dict) else str(f) for f in files]
                logging.info(f"📋 Available filenames ({len(filenames)} total): {filenames[:20]}")  # Show first 20
                logging.info(f"🔍 NAS Search: Looking for '{search_name}' in {len(files)} files in {shop_name}/{template_relative_path}")
            else:
                logging.error(f"❌ No files returned from NAS in {shop_name}/{template_relative_path}")

            matched = False
            for file_info in files:
                # Extract filename from the file info dictionary
                filename = file_info.get('filename', '') if isinstance(file_info, dict) else str(file_info)

                if filename.lower().endswith(extensions):
                    # Try each pattern until we find a match
                    for i, pattern in enumerate(patterns):
                        match_result = pattern.search(filename)
                        if match_result:
                            logging.info(f"✅ NAS Match Found! '{filename}' matched pattern #{i}: '{pattern.pattern}' at position {match_result.span()}")
                            # Return the relative path that can be used for NAS operations
                            return f"{template_name}/{filename}"

                    # Log FIRST failing file with detailed pattern info
                    if not matched:
                        logging.error(f"❌ PATTERN MISMATCH DEBUG:")
                        logging.error(f"   Searching for: '{search_name}'")
                        logging.error(f"   Filename: '{filename}'")
                        logging.error(f"   All patterns: {[p.pattern for p in patterns]}")
                        # Test each pattern manually
                        for i, pattern in enumerate(patterns):
                            test_result = pattern.search(filename)
                            logging.error(f"   Pattern #{i} '{pattern.pattern}': {'MATCH' if test_result else 'NO MATCH'}")
                        matched = True  # Only log once

            # Only log if no match was found at all
            if not matched:
                logging.error(f"❌ NAS Search FAILED: No file found matching '{search_name}' in {shop_name}/{template_relative_path}")
                logging.error(f"   Searched {len(files)} files with {len(patterns)} patterns")
                logging.error(f"   Patterns used: {[p.pattern for p in patterns]}")
        except Exception as e:
            logging.error(f"Error searching NAS for images: {e}")

        return None

    def find_design_in_db(self, search_name, user_id, template_name=None):
        """
        Search for design file in database using fuzzy matching with PostgreSQL pattern matching.
        Returns file_path if found, None otherwise.

        Args:
            search_name: Name to search for (e.g., "UV 632")
            user_id: User ID to filter designs
            template_name: Optional template name to filter by

        Returns:
            str: File path from database if found, None otherwise
        """
        if not self.db:
            logging.warning("No database session available for design lookup")
            return None

        # Normalize whitespace in search name
        import re as regex_module
        normalized_search = regex_module.sub(r'\s+', ' ', search_name.strip())

        from server.src.entities.designs import DesignImages

        try:
            # Base query
            base_query = self.db.query(DesignImages).filter(
                DesignImages.user_id == user_id,
                DesignImages.is_active == True
            )

            # Optionally filter by template
            if template_name:
                from server.src.entities.template import EtsyProductTemplate
                base_query = base_query.join(DesignImages.product_templates).filter(
                    EtsyProductTemplate.name == template_name
                )

            # Strategy 1: Exact substring match (case-insensitive) using PostgreSQL ILIKE
            # ILIKE is PostgreSQL's case-insensitive LIKE operator
            design = base_query.filter(
                DesignImages.filename.ilike(f'%{normalized_search}%')
            ).first()

            if design:
                logging.info(f"DB Search: Found exact match - '{design.filename}' for '{normalized_search}'")
                return design.file_path

            # Strategy 2: Match without spaces (e.g., "UV 632" -> "UV632")
            no_space_search = normalized_search.replace(" ", "")
            design = base_query.filter(
                DesignImages.filename.ilike(f'%{no_space_search}%')
            ).first()

            if design:
                logging.info(f"DB Search: Found no-space match - '{design.filename}' for '{normalized_search}'")
                return design.file_path

            # Strategy 3: Just the number part (for "UV 632" -> "632")
            parts = normalized_search.split(" ")
            if len(parts) > 1 and parts[1].isdigit():
                design = base_query.filter(
                    DesignImages.filename.ilike(f'%{parts[1]}%')
                ).first()

                if design:
                    logging.info(f"DB Search: Found number match - '{design.filename}' for '{normalized_search}'")
                    return design.file_path

            # Strategy 4: Flexible matching with regex (allows spaces, underscores, hyphens)
            # Convert "UV 632" to a pattern like "UV[\s_-]*632"
            flexible_pattern = normalized_search.replace(" ", r"[\s_-]*")
            design = base_query.filter(
                DesignImages.filename.op('~*')(flexible_pattern)  # ~* is case-insensitive regex in PostgreSQL
            ).first()

            if design:
                logging.info(f"DB Search: Found flexible match - '{design.filename}' for '{normalized_search}'")
                return design.file_path

            # Show what files ARE in the database for this template (for debugging)
            all_designs = base_query.limit(10).all()
            if all_designs:
                sample_files = [d.filename for d in all_designs]
                logging.debug(f"DB Search: Sample files in template '{template_name}': {sample_files}")
            else:
                logging.warning(f"DB Search: No files found in database for template '{template_name}'")

            logging.warning(f"DB Search: No match found for '{normalized_search}' in template '{template_name}'")
            return None

        except Exception as e:
            logging.error(f"Error searching database for design: {e}", exc_info=True)
            return None

    def fetch_open_orders_items_nas(self, shop_name, template_name):
        """
        NAS-compatible version of fetch_open_orders_items that uses database lookup first,
        then batch downloads from NAS. This is much more efficient than searching NAS for each item.

        Args:
            shop_name: Shop name for NAS path
            template_name: Template name (item_type) to use

        Returns:
            Dict: Item summary with design file information from NAS
        """
        self.require_authentication()
        self.ensure_valid_token()

        if not nas_storage.enabled:
            logging.error("NAS storage not enabled, cannot fetch orders with NAS support")
            return None

        print(f"\n--- Fetching Open Orders Items (DB-First Mode) for {shop_name}/{template_name} ---")

        receipts_url = f"https://openapi.etsy.com/v3/application/shops/{self.shop_id}/receipts?was_paid=true&was_shipped=false&was_canceled=false"
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        }

        resp = self.session.get(receipts_url, headers=headers)
        if resp.status_code != 200:
            print(f"Failed to fetch open orders: {resp.text} with status code {resp.status_code}")
            return None

        receipts = resp.json().get('results', [])
        item_summary = {}
        item_summary[template_name] = {'Title': [], 'Size': [], 'Total': []}
        item_summary["Total QTY"] = 0

        for receipt in receipts:
            receipt_id = receipt['receipt_id']
            transactions_url = f"https://openapi.etsy.com/v3/application/shops/{self.shop_id}/receipts/{receipt_id}/transactions"
            t_resp = self.session.get(transactions_url, headers=headers)

            if t_resp.status_code != 200:
                print(f"Failed to fetch transactions for receipt {receipt_id}: {t_resp.text} with status code {t_resp.status_code}")
                continue

            transactions = t_resp.json().get('results', [])
            for t in transactions:
                title = t.get('title', 'Unknown')
                quantity = t.get('quantity', 0)
                search_term = title.split(" | ")[0]

                # Try database lookup first (much faster)
                design_file_path = self.find_design_in_db(search_term, self.user_id, template_name)

                # Fallback to NAS search if not in database
                if not design_file_path:
                    logging.debug(f"Design not in DB, searching NAS for: {search_term}")
                    design_file_path = self.find_images_by_name_nas(search_term, shop_name, template_name)

                if design_file_path:
                    i = self._find_index(item_summary[template_name]['Title'], design_file_path)
                    if i >= 0:
                        item_summary[template_name]['Total'][i] += quantity
                    else:
                        item_summary[template_name]['Title'].append(design_file_path)
                        item_summary[template_name]['Size'].append("")
                        item_summary[template_name]['Total'].append(quantity)
                    item_summary["Total QTY"] += quantity
                else:
                    logging.warning(f"No design file found in DB or NAS for order item: {title}")
                    # Still add to item summary but with a placeholder path so gang sheets can be processed
                    placeholder_path = f"{template_name}/MISSING_{search_term.replace(' ', '_')}.png"
                    i = self._find_index(item_summary[template_name]['Title'], placeholder_path)
                    if i >= 0:
                        item_summary[template_name]['Total'][i] += quantity
                    else:
                        item_summary[template_name]['Title'].append(placeholder_path)
                        item_summary[template_name]['Size'].append("")
                        item_summary[template_name]['Total'].append(quantity)
                    item_summary["Total QTY"] += quantity

        print("\nOpen Orders Item Summary (DB-First):")
        for k, v in item_summary[template_name].items():
            print(f"{k}: {v}")

        return item_summary

    def upload_listing_file(self, listing_id: int, file_path: str, file_name: str) -> dict:
        """
        Upload a digital file to a digital listing (supports both local and NAS paths)

        Args:
            listing_id (int): The ID of the listing to add the file to
            file_path (str): Path to the digital file (local or NAS path)
            file_name (str): The name of the file to show on Etsy
        Returns:
            dict: Response from Etsy API
        """
        endpoint = f"{self.base_url}/application/shops/{self.shop_id}/listings/{listing_id}/files"
        headers = {
            "x-api-key": self.client_id,
            "Authorization": f"Bearer {self.oauth_token}"
        }

        # Check if running in production and path is NAS
        is_production = os.getenv('RAILWAY_ENVIRONMENT_NAME') or os.getenv('DOCKER_ENV')

        if is_production and file_path.startswith('/share/'):
            # Load from NAS
            try:
                from server.src.utils.nas_storage import nas_storage
                logging.info(f"Loading digital file from NAS for Etsy upload: {file_path}")

                # Extract shop_name and relative_path from full path
                # Path format: /share/Graphics/ShopName/RelativePath
                path_parts = file_path.split('/')
                if len(path_parts) >= 4 and path_parts[2] == 'Graphics':
                    shop_name = path_parts[3]
                    relative_path = '/'.join(path_parts[4:])

                    # Download file to memory
                    file_content = nas_storage.download_file_to_memory(shop_name, relative_path)
                    if file_content:
                        files = {
                            'file': (file_name, file_content, 'application/octet-stream'),
                            'name': (None, file_name)
                        }
                        response = self.session.post(endpoint, headers=headers, files=files)
                        response.raise_for_status()
                        logging.info(f"Successfully uploaded digital file from NAS to Etsy listing {listing_id}")
                        return response.json()
                    else:
                        raise Exception(f"Failed to download digital file from NAS: {file_path}")
                else:
                    raise Exception(f"Invalid NAS path format: {file_path}")
            except Exception as e:
                logging.error(f"Error loading digital file from NAS: {str(e)}")
                raise
        else:
            # Load from local filesystem
            with open(file_path, 'rb') as file_obj:
                files = {
                    'file': (file_name, file_obj, 'application/octet-stream'),
                    'name': (None, file_name)
                }
                response = self.session.post(endpoint, headers=headers, files=files)
                response.raise_for_status()
                return response.json()

    def fetch_order_summary(self, model, was_shipped=None, was_paid=None, was_canceled=None) -> dict:
        """
        Fetch order summary with optional status filters.

        Args:
            model: Model class for response formatting
            was_shipped: Filter by shipped status ('true', 'false', or None for all)
            was_paid: Filter by paid status ('true', 'false', or None for all)
            was_canceled: Filter by canceled status ('true', 'false', or None for all)

        Returns:
            Dictionary with orders, count, and total
        """
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
        }
        logging.info(f"Using shop ID: {self.shop_id}")
        receipts_url = f"{self.base_url}/application/shops/{self.shop_id}/receipts"

        # Build params with only specified filters
        params = {
            'limit': 100,
            'offset': 0,
        }

        # Add filters only if specified (None means don't filter)
        if was_paid is not None:
            params['was_paid'] = was_paid
        if was_shipped is not None:
            params['was_shipped'] = was_shipped
        if was_canceled is not None:
            params['was_canceled'] = was_canceled

        response = self.session.get(receipts_url, headers=headers, params=params)
        if not response.ok:
            logging.error(f"Failed to fetch orders: {response.status_code} {response.text}")
            return {"success_code": 200, "message": f"Failed to fetch orders: {response.text}"}
        receipts_data = response.json()
        orders = []
        for receipt in receipts_data.get('results', []):
            items = [
                model.OrderItem(
                    title=transaction.get('title', 'N/A'),
                    quantity=transaction.get('quantity', 0),
                    price=float(transaction.get('price', {}).get('amount', 0)),
                    listing_id=transaction.get('listing_id')
                )
                for transaction in receipt.get('transactions', [])
            ]
            order = model.Order(
                order_id=receipt.get('receipt_id'),
                order_date=receipt.get('created_timestamp'),
                shipping_method=receipt.get('shipping_carrier', 'N/A'),
                shipping_cost=float(receipt.get('total_shipping_cost', {}).get('amount', 0)),
                customer_name=receipt.get('name', 'N/A'),
                items=items
            )
            orders.append(order)
        return {"orders":  orders, "count": len(orders), "total": receipts_data.get('count', 0), "success_code": 200}

    def get_shop_listings(self, state: str = "active", limit: int = 100, offset: int = 0, include_images: bool = True) -> dict:
        """
        Get all shop listings with optional filtering by state
        
        Args:
            state (str): Filter by listing state ('active', 'draft', 'expired', etc.)
            limit (int): Number of listings to return (max 100)
            offset (int): Number of listings to skip for pagination
            include_images (bool): Whether to include listing images
            
        Returns:
            dict: Response containing listings data with images
        """
        self.ensure_valid_token()
        logging.info(f"Using shop_id: {self.shop_id}")
        logging.info(f"OAuth token exists: {bool(self.oauth_token)}")
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
        }

        url = f"{self.base_url}/application/shops/{self.shop_id}/listings"
        params = {
            'limit': min(limit, 100),  # Etsy max is 100
            'offset': offset,
            'state': state
        }
        
        # Add includes parameter to get images
        if include_images:
            params['includes'] = 'Images'
        
        try:
            logging.info(f"Making Etsy API request: {url} with params: {params}")
            response = self.session.get(url, headers=headers, params=params)
            logging.info(f"Etsy API response status: {response.status_code}")
            response.raise_for_status()
            listings_data = response.json()

            results_count = len(listings_data.get('results', []))
            total_count = listings_data.get('count', 0)
            logging.info(f"Etsy API returned {results_count} listings out of {total_count} total")

            if results_count > 0:
                first_listing = listings_data.get('results', [{}])[0]
                logging.info(f"First listing keys: {list(first_listing.keys()) if isinstance(first_listing, dict) else 'Not a dict'}")
                if 'Images' in first_listing:
                    logging.info(f"First listing has {len(first_listing['Images'])} images")
                elif 'images' in first_listing:
                    logging.info(f"First listing has {len(first_listing['images'])} images")
                else:
                    logging.info("First listing has no Images or images key")

            # If images are included, they should be in the response
            # If not included via the includes parameter, we need to fetch them separately
            if include_images and 'includes' not in params:
                logging.info("Adding images to listings separately...")
                self._add_images_to_listings(listings_data.get('results', []), headers)

            return listings_data
        except Exception as e:
            logging.error(f"Failed to fetch shop listings: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to fetch shop listings: {e}")

    def get_listing_by_id(self, listing_id: int) -> dict:
        """
        Get a specific listing by ID
        
        Args:
            listing_id (int): The listing ID to fetch
            
        Returns:
            dict: Listing data
        """
        self.ensure_valid_token()
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
        }
        
        url = f"{self.base_url}/application/listings/{listing_id}"
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to fetch listing {listing_id}: {e}")
            raise Exception(f"Failed to fetch listing {listing_id}: {e}")

    def update_listing(self, listing_id: int, update_data: dict) -> dict:
        """
        Update a specific listing
        
        Args:
            listing_id (int): The listing ID to update
            update_data (dict): Fields to update (title, description, price, etc.)
            
        Returns:
            dict: Updated listing data
        """
        self.ensure_valid_token()
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/application/shops/{self.shop_id}/listings/{listing_id}"
        
        try:
            response = self.session.patch(url, headers=headers, json=update_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to update listing {listing_id}: {e}")
            raise Exception(f"Failed to update listing {listing_id}: {e}")

    def bulk_update_listings(self, listing_updates: List[dict]) -> dict:
        """
        Update multiple listings in bulk
        
        Args:
            listing_updates (List[dict]): List of updates, each containing 'listing_id' and update fields
            
        Returns:
            dict: Results of bulk update operation
        """
        results = {
            'successful': [],
            'failed': [],
            'total': len(listing_updates)
        }
        
        for update in listing_updates:
            listing_id = update.pop('listing_id')  # Remove listing_id from update data
            try:
                updated_listing = self.update_listing(listing_id, update)
                results['successful'].append({
                    'listing_id': listing_id,
                    'data': updated_listing
                })
            except Exception as e:
                results['failed'].append({
                    'listing_id': listing_id,
                    'error': str(e)
                })
        
        return results

    def _add_images_to_listings(self, listings: list, headers: dict) -> None:
        """
        Helper method to add images to listings if not already included
        """
        for listing in listings:
            listing_id = listing.get('listing_id')
            if listing_id and 'images' not in listing:
                try:
                    images_url = f"{self.base_url}/application/listings/{listing_id}/images"
                    images_response = self.session.get(images_url, headers=headers)
                    if images_response.status_code == 200:
                        images_data = images_response.json()
                        listing['images'] = images_data.get('results', [])
                    else:
                        listing['images'] = []
                except Exception as e:
                    logging.warning(f"Failed to fetch images for listing {listing_id}: {e}")
                    listing['images'] = []

    def get_all_shop_listings(self, state: str = "active", include_images: bool = True) -> dict:
        """
        Get ALL shop listings by paginating through all pages
        
        Args:
            state (str): Filter by listing state ('active', 'draft', 'expired', etc.)
            include_images (bool): Whether to include listing images
            
        Returns:
            dict: All listings data with images
        """
        all_listings = []
        offset = 0
        limit = 100  # Max per request
        
        while True:
            response = self.get_shop_listings(state=state, limit=limit, offset=offset, include_images=include_images)
            listings = response.get('results', [])
            all_listings.extend(listings)
            
            # Check if we have more pages
            total_count = response.get('count', 0)
            if offset + limit >= total_count:
                break
                
            offset += limit
        
        return {
            'results': all_listings,
            'count': len(all_listings),
            'total': len(all_listings)
        }

    def get_all_active_listings_images(self) -> list:
        """
        Get all active listings with their images for the design gallery

        Returns:
            list: List of listings with images formatted for gallery display
        """
        try:
            logging.info("Calling get_all_shop_listings...")
            response = self.get_all_shop_listings(state="active", include_images=True)
            logging.info(f"get_all_shop_listings returned: {type(response)} with keys: {response.keys() if isinstance(response, dict) else 'N/A'}")

            results = response.get('results', [])
            logging.info(f"Found {len(results)} listings in response")

            listings_with_images = []

            for i, listing in enumerate(results):
                if isinstance(listing, dict):
                    listing_id = listing.get('listing_id')
                    listing_title = listing.get('title', 'Untitled')

                    # Check both 'Images' and 'images' keys
                    images = listing.get('Images', []) or listing.get('images', [])

                    logging.info(f"Listing {i+1}: ID={listing_id}, Title='{listing_title}', Images count={len(images)}")
                    logging.info(f"Listing keys: {list(listing.keys())}")

                    if images:  # Only include listings that have images
                        listings_with_images.append({
                            'listing_id': listing_id,
                            'title': listing_title,
                            'images': images
                        })
                        logging.info(f"Added listing {listing_id} with {len(images)} images")
                    else:
                        logging.info(f"Skipped listing {listing_id} - no images found")
                else:
                    logging.warning(f"Listing {i+1} is not a dict: {type(listing)}")

            logging.info(f"Returning {len(listings_with_images)} listings with images")
            return listings_with_images
        except Exception as e:
            logging.error(f"Failed to fetch active listings with images: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return []

    def get_shop_receipts_with_items(self, shop_id, limit=100, offset=0, was_shipped=None, was_paid=None, was_canceled=None):
        """
        Get shop receipts (orders) with transaction items.

        Args:
            shop_id: Shop ID
            limit: Maximum number of receipts to return
            offset: Number of receipts to skip (for pagination)
            was_shipped: Filter by shipped status ('true', 'false', or None for all)
            was_paid: Filter by paid status ('true', 'false', or None for all)
            was_canceled: Filter by canceled status ('true', 'false', or None for all)

        Returns:
            Dictionary with results and count
        """
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
        }

        receipts_url = f"{self.base_url}/application/shops/{shop_id}/receipts"
        params = {
            'limit': min(limit, 100),  # Etsy API max is 100
            'offset': offset,
        }

        # Add filters only if specified (None means don't filter)
        if was_paid is not None:
            params['was_paid'] = was_paid
        if was_shipped is not None:
            params['was_shipped'] = was_shipped
        if was_canceled is not None:
            params['was_canceled'] = was_canceled

        response = self.session.get(receipts_url, headers=headers, params=params)
        if not response.ok:
            logging.error(f"Failed to fetch receipts: {response.status_code} {response.text}")
            return None

        return response.json()

    def fetch_selected_order_items(self, shop_id, order_ids, template_name, shop_name=None):
        """
        Fetch items from specific selected orders and process them for gang sheet creation.

        Args:
            shop_id: Shop ID
            order_ids: List of order/receipt IDs to fetch
            template_name: Template name to filter items
            shop_name: Shop name for NAS lookup (optional)

        Returns:
            Dictionary formatted for gang sheet creation with Title, Size, Total arrays
        """
        # Store shop_name for use in find_design_for_item
        self.shop_name = shop_name
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
        }

        # Initialize result structure
        image_data = {
            'Title': [],
            'Size': [],
            'Total': []
        }

        processed_items = 0

        # Fetch each order
        for order_id in order_ids:
            try:
                receipt_url = f"{self.base_url}/application/shops/{shop_id}/receipts/{order_id}"
                response = self.session.get(receipt_url, headers=headers)

                if not response.ok:
                    logging.warning(f"Failed to fetch order {order_id}: {response.status_code}")
                    continue

                receipt = response.json()

                # Log order details with full diagnostic info
                transactions = receipt.get('transactions', [])
                was_shipped = receipt.get('was_shipped', False)
                was_paid = receipt.get('was_paid', False)

                logging.info(f"📦 Order {order_id}: Found {len(transactions)} items | shipped: {was_shipped} | paid: {was_paid}")

                # Log full receipt data for debugging completed orders
                if was_shipped:
                    logging.debug(f"🔍 Full receipt data for shipped order {order_id}: {receipt}")

                # Check if transactions list is empty
                if not transactions:
                    logging.warning(f"⚠️ Order {order_id} returned ZERO transactions! Receipt keys: {list(receipt.keys())}")
                    logging.warning(f"⚠️ Full receipt: {receipt}")

                # Process each transaction in the order
                for idx, transaction in enumerate(transactions, 1):
                    item_title = transaction.get('title', '')
                    quantity = transaction.get('quantity', 1)
                    transaction_id = transaction.get('transaction_id', 'unknown')

                    logging.info(f"  Processing item {idx}/{len(transactions)} from order {order_id}: '{item_title}' (qty: {quantity}, tx_id: {transaction_id})")

                    # Try to find design file for this item
                    design_path = self.find_design_for_item(item_title, template_name)

                    if design_path:
                        # Check if this design already exists in our data
                        # If so, add to its quantity instead of creating a duplicate entry
                        if design_path in image_data['Title']:
                            # Find the index and add to existing quantity
                            existing_idx = image_data['Title'].index(design_path)
                            image_data['Total'][existing_idx] += quantity
                            logging.info(f"  ✅ Updated existing item: {item_title} (added qty: {quantity}, total now: {image_data['Total'][existing_idx]}) -> {design_path}")
                        else:
                            # New design, add to arrays
                            image_data['Title'].append(design_path)
                            image_data['Size'].append(template_name)
                            image_data['Total'].append(quantity)
                            logging.info(f"  ✅ Added new item from order {order_id}: {item_title} (qty: {quantity}) -> {design_path}")
                        processed_items += 1
                    else:
                        logging.warning(f"  ❌ No design found for item: {item_title}")

            except Exception as e:
                logging.error(f"Error processing order {order_id}: {e}")
                continue

        logging.info(f"Processed {processed_items} items from {len(order_ids)} selected orders")

        return {
            'items': processed_items,
            **image_data
        }

    def find_design_for_item(self, item_title, template_name):
        """
        Find design file path for an item title.

        Args:
            item_title: Item title from order (e.g., "UV 840 | UVDTF Cup wrap | ...")
            template_name: Template name

        Returns:
            Design file path or None
        """
        import re

        # Extract just the design number from the title
        # Pattern matches "UV XXX" or "UV XXX |" at the start of the title
        search_name = item_title
        match = re.match(r'^(UV\s*\d+)', item_title.strip(), re.IGNORECASE)
        if match:
            search_name = match.group(1).strip()
            logging.info(f"🔍 Extracted design number '{search_name}' from title '{item_title}'")
        else:
            logging.warning(f"⚠️ Could not extract UV number from title: '{item_title}'")

        # Try database first with extracted design number
        logging.info(f"🔍 Searching database for '{search_name}' in template '{template_name}'")
        design_path = self.find_design_in_db(search_name, self.user_id, template_name)

        if design_path:
            logging.info(f"✅ Found in database: {design_path}")
            return design_path

        # Try NAS if database lookup failed
        logging.info(f"🔍 Database search failed, trying NAS for '{search_name}'")
        if hasattr(self, 'shop_name') and self.shop_name:
            design_path = self.find_images_by_name_nas(
                search_name,
                self.shop_name,
                template_name
            )
            if design_path:
                logging.info(f"✅ Found on NAS: {design_path}")
            else:
                logging.warning(f"❌ Not found on NAS for '{search_name}'")
        else:
            logging.warning(f"⚠️ Cannot search NAS - shop_name not available")

        return design_path