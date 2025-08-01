import requests, os, json, hashlib, base64, secrets, random, csv, sys, time, re
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv, set_key
from urllib.parse import urlencode
from collections import deque

# Get the project root directory (2 levels up from this file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

class EtsyAPI:
    def __init__(self):
        """
        Initialize the Etsy listing uploader with OAuth credentials
        
        Args:
            client_id (str): Your Etsy OAuth client ID
            client_secret (str): Your Etsy OAuth client secret
            shop_id (str): Your Etsy shop ID
        """
        self.session = requests.Session()
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.base_url = "https://openapi.etsy.com/v3"
        self.oauth_token = os.getenv('ETSY_OAUTH_TOKEN')
        self.refresh_token = os.getenv('ETSY_REFRESH_TOKEN')
        self.token_expiry = float(os.getenv('ETSY_OAUTH_TOKEN_EXPIRY', '0'))
        self.ping_url = "https://api.etsy.com/v3/application/openapi-ping"
        self.access_token = None
        # self.oauth_token = None
        # Authenticate with correct scopes if needed
        self.authenticate_with_scopes()
        
        # Get shop ID from environment or fetch it automatically
        self.shop_id = os.getenv('SHOP_ID')
        # self.shop_id = None
        if not self.shop_id:
            self.shop_id = self.fetch_user_shop_id()
            if self.shop_id:
                print(f"Using shop ID: {self.shop_id}")
            else:
                raise Exception("Could not fetch shop ID. Please set SHOP_ID in your .env file.")
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

    def fetch_user_shop_id(self):
        self.ensure_valid_token()
        """Fetch the user's shop ID from the Etsy API"""
        url = 'https://openapi.etsy.com/v3/application/shops?shop_name=NookTransfers'
        headers = {
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        }
        try:
            resp = self.session.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                shops = data.get('results', [])
                if shops:
                    return str(shops[0]['shop_id'])  # Return the first shop's ID
                else:
                    print("No shops found for this user.")
                    return None
            else:
                print(f"Failed to fetch shops: {resp.text}")
                return None
        except Exception as e:
            print(f"Error fetching shop ID: {e}")
            return None

    def create_draft_listing(self, title: str, description: str, price: float, 
                           quantity: int, tags: List[str], 
                           materials: List[str],
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
            response = requests.post(endpoint, headers=headers, files=files)
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
        pattern = re.compile(search_name, re.IGNORECASE)
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
            response = requests.post(endpoint, headers=headers, files=files)
            response.raise_for_status()
            return response.json()