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
        'QNAP_HTTP_PORT',
        'QNAP_WEB_PORT',
        'QNAP_USE_HTTPS'
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

def test_http_connection():
    """Test HTTP connection (qnap_client.py)"""
    logger.info("\n=== Testing HTTP Connection (qnap_client.py) ===")

    try:
        from server.src.utils.qnap_client import qnap_client
        if not qnap_client.enabled:
            logger.warning("QNAP HTTP client is disabled")
            return False

        # Try to authenticate
        auth_result = qnap_client._authenticate()
        if auth_result:
            logger.info("QNAP HTTP authentication successful")

            # Try to download a test file
            test_path = "/share/Graphics/NookTransfers/Mockups/BaseMockups/UVDTF 16oz/mockup_52f0959b-5358-4684-80b5-90b8e89d559b_2.png"
            file_data = qnap_client.download_file(test_path)

            if file_data:
                logger.info(f"HTTP download successful. File size: {len(file_data)} bytes")
                return True
            else:
                logger.error("HTTP download failed - no data returned")
                return False
        else:
            logger.error("QNAP HTTP authentication failed")
            return False

    except Exception as e:
        logger.error(f"HTTP connection failed: {e}")
        return False

def main():
    logger.info("QNAP Connection Test Script")
    logger.info("=" * 50)

    # Test environment variables
    env_ok = test_environment_variables()
    if not env_ok:
        logger.error("Required QNAP environment variables are missing!")
        return False

    # Test both connection methods
    sftp_ok = test_sftp_connection()
    http_ok = test_http_connection()

    logger.info("\n=== Test Results ===")
    logger.info(f"Environment Variables: {'✓' if env_ok else '✗'}")
    logger.info(f"SFTP Connection: {'✓' if sftp_ok else '✗'}")
    logger.info(f"HTTP Connection: {'✓' if http_ok else '✗'}")

    if sftp_ok and http_ok:
        logger.info("✓ All QNAP connections working correctly!")
        return True
    else:
        logger.error("✗ Some QNAP connections failed. Check logs above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)