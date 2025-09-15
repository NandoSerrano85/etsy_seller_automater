"""
QNAP NAS Client for Railway Production
Accesses QNAP NAS files via HTTP/HTTPS for Railway compatibility
"""
import os
import logging
import requests
import io
from typing import Optional, BinaryIO
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
        self.qnap_port = os.getenv('QNAP_PORT', '443')  # HTTPS by default
        self.use_https = os.getenv('QNAP_USE_HTTPS', 'true').lower() == 'true'
        self.session = requests.Session()
        self.authenticated = False

        if not all([self.qnap_host, self.qnap_username, self.qnap_password]):
            logger.warning("QNAP credentials not configured. QNAP file access will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"QNAP client initialized for host: {self.qnap_host}")

    def _authenticate(self) -> bool:
        """Authenticate with QNAP NAS"""
        if not self.enabled or self.authenticated:
            return self.authenticated

        protocol = 'https' if self.use_https else 'http'
        auth_url = f"{protocol}://{self.qnap_host}:{self.qnap_port}/cgi-bin/authLogin.cgi"

        auth_data = {
            'user': self.qnap_username,
            'pwd': self.qnap_password
        }

        try:
            logger.info("Authenticating with QNAP NAS...")
            response = self.session.post(auth_url, data=auth_data, timeout=30, verify=False)

            if response.status_code == 200 and 'authPassed' in response.text:
                self.authenticated = True
                logger.info("QNAP authentication successful")
                return True
            else:
                logger.error(f"QNAP authentication failed: {response.status_code}")
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

        # Convert local path to QNAP web path
        # /share/Graphics/... -> /share_name/Graphics/...
        web_path = qnap_path.replace('/share/', '/')

        protocol = 'https' if self.use_https else 'http'
        download_url = f"{protocol}://{self.qnap_host}:{self.qnap_port}/cgi-bin/filemanager/utilRequest.cgi"

        params = {
            'func': 'download',
            'path': web_path,
            'sid': self.session.cookies.get('NAS_SID', '')
        }

        try:
            logger.info(f"Downloading from QNAP: {qnap_path}")
            response = self.session.get(download_url, params=params, timeout=60, verify=False)

            if response.status_code == 200:
                logger.info(f"Successfully downloaded: {qnap_path} ({len(response.content)} bytes)")
                return response.content
            else:
                logger.error(f"QNAP download failed: {response.status_code} for {qnap_path}")
                return None

        except Exception as e:
            logger.error(f"QNAP download error for {qnap_path}: {e}")
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