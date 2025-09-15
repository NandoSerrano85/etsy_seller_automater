"""
QNAP NAS Client for Railway Production
Accesses QNAP NAS files via HTTP/HTTPS for Railway compatibility
"""
import os
import logging
import requests
import io
from typing import Optional
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

class QNAPClient:
    """Client for accessing QNAP NAS files via HTTP/HTTPS in Railway production"""

    def __init__(self):
        self.qnap_host = os.getenv('QNAP_HOST')
        self.qnap_username = os.getenv('QNAP_USERNAME')
        self.qnap_password = os.getenv('QNAP_PASSWORD')
        # Use separate port for HTTP client (default 8080) vs SFTP (port 22)
        self.qnap_port = os.getenv('QNAP_HTTP_PORT', os.getenv('QNAP_WEB_PORT', '8080'))
        self.use_https = os.getenv('QNAP_USE_HTTPS', 'false').lower() == 'true'  # Default to HTTP
        self.session = requests.Session()
        self.authenticated = False

        # Disable SSL verification for QNAP (often uses self-signed certs)
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        if not all([self.qnap_host, self.qnap_username, self.qnap_password]):
            logger.warning("QNAP credentials not configured. QNAP file access will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            protocol = 'https' if self.use_https else 'http'
            logger.info(f"QNAP HTTP client initialized for {protocol}://{self.qnap_host}:{self.qnap_port}")
            logger.info(f"QNAP environment: HOST={self.qnap_host}, HTTP_PORT={self.qnap_port}, HTTPS={self.use_https}")

    def _authenticate(self) -> bool:
        """Authenticate with QNAP NAS"""
        if not self.enabled or self.authenticated:
            return self.authenticated

        protocol = 'https' if self.use_https else 'http'

        # Try multiple authentication endpoints (QNAP has different APIs)
        auth_endpoints = [
            f"{protocol}://{self.qnap_host}:{self.qnap_port}/cgi-bin/authLogin.cgi",
            f"{protocol}://{self.qnap_host}:{self.qnap_port}/cgi-bin/login.cgi",
            f"{protocol}://{self.qnap_host}:{self.qnap_port}/api/auth/login"
        ]

        auth_data_variants = [
            {'user': self.qnap_username, 'pwd': self.qnap_password},
            {'username': self.qnap_username, 'password': self.qnap_password},
            {'account': self.qnap_username, 'pwd': self.qnap_password}
        ]

        try:
            logger.info(f"Authenticating with QNAP NAS at {self.qnap_host}:{self.qnap_port}...")

            for auth_url in auth_endpoints:
                for auth_data in auth_data_variants:
                    try:
                        logger.info(f"Trying auth URL: {auth_url}")
                        response = self.session.post(auth_url, data=auth_data, timeout=15)

                        if response.status_code == 200:
                            response_text = response.text.lower()
                            # Check for various success indicators
                            if any(indicator in response_text for indicator in ['authpassed', 'success', 'true', 'ok']):
                                self.authenticated = True
                                logger.info("QNAP authentication successful")
                                return True
                            elif 'sid' in response.cookies or 'NAS_SID' in response.cookies:
                                self.authenticated = True
                                logger.info("QNAP authentication successful (got session cookie)")
                                return True

                    except Exception as e:
                        logger.debug(f"Auth attempt failed for {auth_url}: {e}")
                        continue

            logger.error("All QNAP authentication methods failed")
            return False

        except Exception as e:
            logger.error(f"QNAP authentication error: {e}")
            return False

    def download_file(self, qnap_path: str) -> Optional[bytes]:
        """Download file from QNAP NAS"""
        if not self.enabled:
            logger.warning(f"QNAP client disabled - cannot download: {qnap_path}")
            return None

        if not self._authenticate():
            logger.error("QNAP authentication failed - cannot download file")
            return None

        # Convert local path to web accessible path
        # /share/Graphics/... -> /Graphics/... or /share/Graphics/...
        web_path = qnap_path
        if web_path.startswith('/share/'):
            web_path = web_path[6:]  # Remove '/share' prefix

        protocol = 'https' if self.use_https else 'http'

        # Try multiple download methods for QNAP
        download_methods = [
            # Method 1: File Manager API
            {
                'url': f"{protocol}://{self.qnap_host}:{self.qnap_port}/cgi-bin/filemanager/utilRequest.cgi",
                'params': {
                    'func': 'download',
                    'path': web_path,
                    'sid': self.session.cookies.get('NAS_SID', self.session.cookies.get('sid', ''))
                }
            },
            # Method 2: Direct file access
            {
                'url': f"{protocol}://{self.qnap_host}:{self.qnap_port}{web_path}",
                'params': {}
            },
            # Method 3: Share access
            {
                'url': f"{protocol}://{self.qnap_host}:{self.qnap_port}/share{web_path}",
                'params': {}
            },
            # Method 4: Alternative file manager
            {
                'url': f"{protocol}://{self.qnap_host}:{self.qnap_port}/cgi-bin/file_download.cgi",
                'params': {
                    'file_path': web_path,
                    'sid': self.session.cookies.get('NAS_SID', self.session.cookies.get('sid', ''))
                }
            }
        ]

        for i, method in enumerate(download_methods):
            try:
                logger.info(f"Downloading attempt {i+1}: {method['url']} -> {qnap_path}")
                response = self.session.get(
                    method['url'],
                    params=method['params'],
                    timeout=30
                )

                if response.status_code == 200 and len(response.content) > 0:
                    # Verify it's actually an image file (not an error page)
                    if response.content.startswith(b'\x89PNG') or response.content.startswith(b'\xff\xd8\xff'):
                        logger.info(f"Successfully downloaded: {qnap_path} ({len(response.content)} bytes)")
                        return response.content
                    else:
                        logger.debug(f"Download method {i+1} returned non-image content")

            except Exception as e:
                logger.debug(f"Download method {i+1} failed: {e}")
                continue

        logger.error(f"All QNAP download methods failed for: {qnap_path}")
        return None

    def load_image_cv2(self, qnap_path: str) -> Optional[np.ndarray]:
        """Load image from QNAP NAS as CV2 array"""
        file_data = self.download_file(qnap_path)
        if file_data is None:
            return None

        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(file_data, np.uint8)

            # Decode image
            image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

            if image is not None:
                logger.info(f"Successfully loaded CV2 image from QNAP: {qnap_path}")
                return image
            else:
                logger.error(f"Failed to decode image with CV2: {qnap_path}")

                # Try PIL fallback
                try:
                    pil_image = Image.open(io.BytesIO(file_data))
                    if pil_image.mode == 'RGBA':
                        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGRA)
                    else:
                        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    logger.info(f"Successfully loaded image from QNAP with PIL fallback: {qnap_path}")
                    return image
                except Exception as e:
                    logger.error(f"PIL fallback also failed for {qnap_path}: {e}")
                    return None

        except Exception as e:
            logger.error(f"Error loading image from QNAP {qnap_path}: {e}")
            return None

# Global QNAP client instance
qnap_client = QNAPClient()