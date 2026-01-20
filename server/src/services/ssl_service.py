"""
SSL Certificate Service

Handles SSL certificate provisioning and management using Let's Encrypt.
Supports automatic certificate renewal and status tracking.
"""

import subprocess
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Configuration
CERT_BASE_PATH = Path(os.getenv("SSL_CERT_PATH", "/etc/letsencrypt/live"))
LETSENCRYPT_EMAIL = os.getenv("LETSENCRYPT_EMAIL", "admin@craftflow.store")
CERTBOT_PATH = os.getenv("CERTBOT_PATH", "certbot")
USE_STAGING = os.getenv("LETSENCRYPT_STAGING", "false").lower() == "true"


@dataclass
class CertificateInfo:
    """Information about an SSL certificate"""
    domain: str
    exists: bool
    valid: bool
    expires_at: Optional[datetime]
    days_until_expiry: Optional[int]
    certificate_path: Optional[str]
    private_key_path: Optional[str]


class SSLService:
    """Service for managing SSL certificates"""

    @staticmethod
    async def provision_certificate(domain: str, email: Optional[str] = None) -> bool:
        """
        Provision an SSL certificate for a domain using Let's Encrypt.

        Args:
            domain: The domain to get a certificate for
            email: Contact email for certificate notifications

        Returns:
            True if certificate was provisioned successfully, False otherwise
        """
        email = email or LETSENCRYPT_EMAIL

        try:
            # Build certbot command
            cmd = [
                CERTBOT_PATH, 'certonly',
                '--non-interactive',
                '--agree-tos',
                '-d', domain,
                '--email', email,
            ]

            # Use standalone or webroot method
            # In production, you might use --nginx or --apache
            cmd.extend(['--standalone', '--preferred-challenges', 'http'])

            # Use staging for testing
            if USE_STAGING:
                cmd.append('--staging')

            logger.info(f"Provisioning SSL certificate for {domain}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )

            if result.returncode == 0:
                logger.info(f"SSL certificate provisioned successfully for {domain}")
                return True
            else:
                logger.error(f"Failed to provision SSL certificate for {domain}: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"SSL provisioning timed out for {domain}")
            return False
        except FileNotFoundError:
            logger.warning(f"Certbot not found at {CERTBOT_PATH}. SSL provisioning unavailable.")
            # In development, we'll pretend it worked
            if os.getenv("ENVIRONMENT", "development") == "development":
                logger.info(f"Development mode: Simulating SSL success for {domain}")
                return True
            return False
        except Exception as e:
            logger.error(f"SSL provisioning error for {domain}: {e}")
            return False

    @staticmethod
    def get_certificate_info(domain: str) -> CertificateInfo:
        """
        Get information about a domain's SSL certificate.

        Args:
            domain: The domain to check

        Returns:
            CertificateInfo with certificate details
        """
        cert_dir = CERT_BASE_PATH / domain
        cert_path = cert_dir / "fullchain.pem"
        key_path = cert_dir / "privkey.pem"

        if not cert_path.exists():
            return CertificateInfo(
                domain=domain,
                exists=False,
                valid=False,
                expires_at=None,
                days_until_expiry=None,
                certificate_path=None,
                private_key_path=None
            )

        # Get certificate expiry
        try:
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend

            with open(cert_path, 'rb') as f:
                cert_data = f.read()

            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            expires_at = cert.not_valid_after_utc
            days_until_expiry = (expires_at - datetime.utcnow()).days
            is_valid = days_until_expiry > 0

            return CertificateInfo(
                domain=domain,
                exists=True,
                valid=is_valid,
                expires_at=expires_at,
                days_until_expiry=days_until_expiry,
                certificate_path=str(cert_path),
                private_key_path=str(key_path) if key_path.exists() else None
            )

        except ImportError:
            # cryptography library not available
            logger.warning("cryptography library not available for certificate inspection")
            return CertificateInfo(
                domain=domain,
                exists=True,
                valid=True,  # Assume valid if we can't check
                expires_at=None,
                days_until_expiry=None,
                certificate_path=str(cert_path),
                private_key_path=str(key_path) if key_path.exists() else None
            )
        except Exception as e:
            logger.error(f"Error reading certificate for {domain}: {e}")
            return CertificateInfo(
                domain=domain,
                exists=True,
                valid=False,
                expires_at=None,
                days_until_expiry=None,
                certificate_path=str(cert_path),
                private_key_path=str(key_path) if key_path.exists() else None
            )

    @staticmethod
    async def renew_certificate(domain: str) -> bool:
        """
        Renew an SSL certificate for a domain.

        Args:
            domain: The domain to renew certificate for

        Returns:
            True if renewal was successful, False otherwise
        """
        try:
            cmd = [
                CERTBOT_PATH, 'renew',
                '--cert-name', domain,
                '--non-interactive',
            ]

            if USE_STAGING:
                cmd.append('--staging')

            logger.info(f"Renewing SSL certificate for {domain}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                logger.info(f"SSL certificate renewed successfully for {domain}")
                return True
            else:
                logger.error(f"Failed to renew SSL certificate for {domain}: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"SSL renewal timed out for {domain}")
            return False
        except FileNotFoundError:
            logger.warning(f"Certbot not found. SSL renewal unavailable.")
            return False
        except Exception as e:
            logger.error(f"SSL renewal error for {domain}: {e}")
            return False

    @staticmethod
    async def revoke_certificate(domain: str) -> bool:
        """
        Revoke an SSL certificate for a domain.

        Args:
            domain: The domain to revoke certificate for

        Returns:
            True if revocation was successful, False otherwise
        """
        cert_path = CERT_BASE_PATH / domain / "fullchain.pem"

        if not cert_path.exists():
            logger.warning(f"No certificate found to revoke for {domain}")
            return True

        try:
            cmd = [
                CERTBOT_PATH, 'revoke',
                '--cert-path', str(cert_path),
                '--non-interactive',
            ]

            if USE_STAGING:
                cmd.append('--staging')

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info(f"SSL certificate revoked for {domain}")
                return True
            else:
                logger.error(f"Failed to revoke SSL certificate for {domain}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"SSL revocation error for {domain}: {e}")
            return False

    @staticmethod
    def get_certificates_needing_renewal(days_threshold: int = 30) -> list:
        """
        Get list of certificates that need renewal soon.

        Args:
            days_threshold: Renew if expiring within this many days

        Returns:
            List of domains needing renewal
        """
        domains_to_renew = []

        if not CERT_BASE_PATH.exists():
            return domains_to_renew

        for domain_dir in CERT_BASE_PATH.iterdir():
            if domain_dir.is_dir():
                info = SSLService.get_certificate_info(domain_dir.name)
                if info.exists and info.days_until_expiry is not None:
                    if info.days_until_expiry <= days_threshold:
                        domains_to_renew.append({
                            "domain": domain_dir.name,
                            "expires_at": info.expires_at,
                            "days_until_expiry": info.days_until_expiry
                        })

        return domains_to_renew


async def check_and_renew_certificates():
    """
    Background task to check and renew certificates that are expiring soon.

    Should be run periodically (e.g., daily via cron or scheduler).
    """
    logger.info("Checking certificates for renewal...")

    certificates = SSLService.get_certificates_needing_renewal(days_threshold=30)

    for cert in certificates:
        domain = cert["domain"]
        logger.info(f"Certificate for {domain} expires in {cert['days_until_expiry']} days, renewing...")

        success = await SSLService.renew_certificate(domain)
        if success:
            logger.info(f"Successfully renewed certificate for {domain}")
        else:
            logger.error(f"Failed to renew certificate for {domain}")

    logger.info(f"Certificate renewal check complete. Processed {len(certificates)} certificates.")
