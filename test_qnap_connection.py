#!/usr/bin/env python3
"""
Test script to verify QNAP connection configuration
Run this to debug QNAP connectivity issues
"""

import os
import sys
import logging
from pathlib import Path

# Add server to path for imports
sys.path.insert(0, str(Path(__file__).parent / "server"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test that QNAP environment variables are properly set"""
    logger.info("=== QNAP Environment Variables ===")

    qnap_vars = [
        'QNAP_HOST',
        'QNAP_USERNAME',
        'QNAP_PASSWORD',
        'QNAP_PORT',
        'NAS_BASE_PATH'
    ]

    for var in qnap_vars:
        value = os.getenv(var)
        if var in ['QNAP_PASSWORD']:
            display_value = '***' if value else None
        else:
            display_value = value
        logger.info(f"{var}: {display_value}")

    return all([os.getenv('QNAP_HOST'), os.getenv('QNAP_USERNAME'), os.getenv('QNAP_PASSWORD')])

def test_sftp_connection():
    """Test SFTP connection (nas_storage.py)"""
    logger.info("\n=== Testing SFTP Connection (nas_storage.py) ===")

    try:
        from server.src.utils.nas_storage import nas_storage
        if not nas_storage.enabled:
            logger.warning("NAS storage is disabled")
            return False

        # Try to list a directory
        files = nas_storage.list_files("NookTransfers", "")
        logger.info(f"SFTP connection successful. Found {len(files)} files in NookTransfers directory")
        return True

    except Exception as e:
        logger.error(f"SFTP connection failed: {e}")
        return False

def test_mockup_loading():
    """Test mockup image loading (mockups_util.py)"""
    logger.info("\n=== Testing Mockup Image Loading ===")

    try:
        from server.src.utils.nas_storage import nas_storage
        if not nas_storage.enabled:
            logger.warning("NAS storage is disabled")
            return False

        # Test mockup file download using the same path that was failing
        shop_name = "NookTransfers"
        relative_path = "Mockups/BaseMockups/UVDTF 16oz/mockup_52f0959b-5358-4684-80b5-90b8e89d559b_2.png"

        # Try to download the mockup file to memory
        file_content = nas_storage.download_file_to_memory(shop_name, relative_path)

        if file_content:
            logger.info(f"Mockup download successful. File size: {len(file_content)} bytes")

            # Try to decode as image (same as mockups_util.py)
            import numpy as np
            import cv2
            nparr = np.frombuffer(file_content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

            if image is not None:
                logger.info(f"Image decode successful. Shape: {image.shape}")
                return True
            else:
                logger.error("Image decode failed")
                return False
        else:
            logger.error("Mockup download failed - no data returned")
            return False

    except Exception as e:
        logger.error(f"Mockup loading failed: {e}")
        return False

def main():
    logger.info("QNAP Connection Test Script")
    logger.info("=" * 50)

    # Test environment variables
    env_ok = test_environment_variables()
    if not env_ok:
        logger.error("Required QNAP environment variables are missing!")
        return False

    # Test SFTP connection and mockup loading
    sftp_ok = test_sftp_connection()
    mockup_ok = test_mockup_loading()

    logger.info("\n=== Test Results ===")
    logger.info(f"Environment Variables: {'✓' if env_ok else '✗'}")
    logger.info(f"SFTP Connection: {'✓' if sftp_ok else '✗'}")
    logger.info(f"Mockup Loading: {'✓' if mockup_ok else '✗'}")

    if sftp_ok and mockup_ok:
        logger.info("✓ All QNAP operations working correctly!")
        return True
    else:
        logger.error("✗ Some QNAP operations failed. Check logs above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)