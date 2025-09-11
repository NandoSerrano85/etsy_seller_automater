import requests, os,  hashlib, base64, secrets, time, re, logging
from typing import List, Dict, Optional
from dotenv import load_dotenv, set_key
from urllib.parse import urlencode
from collections import deque
from server.src.entities.third_party_oauth import ThirdPartyOAuthToken

# Get the project root directory (2 levels up from this file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

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
        # Fallback to .env if not found in DB
        if not self.oauth_token:
            self.oauth_token = os.getenv('ETSY_OAUTH_TOKEN')
            self.refresh_token = os.getenv('ETSY_REFRESH_TOKEN')
            self.token_expiry = float(os.getenv('ETSY_OAUTH_TOKEN_EXPIRY', '0'))
        # Authenticate with correct scopes if needed
        self.authenticate_with_scopes()
        # Get shop ID from environment or fetch it automatically
        self.shop_id = self.fetch_user_shop_id()
        if self.shop_id:
            print(f"Using shop ID: {self.shop_id}")
        else:
            raise Exception("Could not fetch shop ID from Etsy API. Please reconnect your Etsy account in the application settings.")
        self.taxonomy_id = self.fetch_taxonomies()
        self.shipping_profile_id = self.fetch_shipping_profiles()
        self.shop_section_id = self.fetch_shop_sections()

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
        resp = self.session.post(token_url, data=data, headers=headers)
        if resp.status_code == 200:
            token_info = resp.json()
            self.oauth_token = token_info.get('access_token')
            self.refresh_token = token_info.get('refresh_token')
            expires_in = token_info.get('expires_in', 3600)
            self.token_expiry = time.time() + expires_in
            # Update .env file
            try:
                set_key(dotenv_path, "ETSY_OAUTH_TOKEN", self.oauth_token)
                set_key(dotenv_path, "ETSY_REFRESH_TOKEN", self.refresh_token)
                set_key(dotenv_path, "ETSY_OAUTH_TOKEN_EXPIRY", str(self.token_expiry))
            except Exception as e:
                print(f"Warning: Could not update .env: {e}")
            print("Access token refreshed and .env updated.")
        else:
            raise Exception(f"Failed to refresh token: {resp.text}")

    def ensure_valid_token(self):
        if self.is_token_expired():
            print("Access token expired or about to expire, refreshing...")
            self.refresh_access_token()

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
        
        if not shops_data or 'results' not in shops_data or not shops_data['results']:
            logging.error(f"No shops found for this user: {shops_data}")
            return None
        
        # Get the first shop's ID
        first_shop = shops_data['results'][0]
        shop_id = first_shop.get('shop_id')
        
        if not shop_id:
            logging.error(f"Shop ID not found in shop data: {first_shop}")
            return None
            
        return shop_id

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
        Upload an image to a listing
        
        Args:
            listing_id (int): The ID of the listing to add the image to
            image_path (str): Path to the image file
        Returns:
            Dict: Response from Etsy API
        """
        endpoint = f"{self.base_url}/application/shops/{self.shop_id}/listings/{listing_id}/images"
        headers = {
            "x-api-key": self.client_id,
            "Authorization": f"Bearer {self.oauth_token}"
        }
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
        for root, dirs, files in os.walk(image_dir):
            for file in files:
                if file.lower().endswith(extensions) and pattern.search(file):
                    full_path = os.path.join(root, file)
                    return full_path

    def upload_listing_file(self, listing_id: int, file_path: str, file_name: str) -> dict:
        """
        Upload a digital file to a digital listing.
        Args:
            listing_id (int): The ID of the listing to add the file to
            file_path (str): Path to the digital file
            file_name (str): The name of the file to show on Etsy
        Returns:
            dict: Response from Etsy API
        """
        endpoint = f"{self.base_url}/application/shops/{self.shop_id}/listings/{listing_id}/files"
        headers = {
            "x-api-key": self.client_id,
            "Authorization": f"Bearer {self.oauth_token}"
        }
        with open(file_path, 'rb') as file_obj:
            files = {
                'file': (file_name, file_obj, 'application/octet-stream'),
                'name': (None, file_name)
            }
            response = self.session.post(endpoint, headers=headers, files=files)
            response.raise_for_status()
            return response.json()

    def fetch_order_summary(self, model) -> dict:
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}',
        }
        logging.info(f"Using shop ID: {self.shop_id}")
        receipts_url = f"{self.base_url}/application/shops/{self.shop_id}/receipts"
        params = {
            'limit': 100,
            'offset': 0,
            'was_paid': 'true',
            'was_shipped': 'false',
            'was_canceled': 'false'
        }
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
            response = self.session.get(url, headers=headers, params=params)
            response.raise_for_status()
            listings_data = response.json()
            
            # If images are included, they should be in the response
            # If not included via the includes parameter, we need to fetch them separately
            if include_images and 'includes' not in params:
                self._add_images_to_listings(listings_data.get('results', []), headers)
            
            return listings_data
        except Exception as e:
            logging.error(f"Failed to fetch shop listings: {e}")
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