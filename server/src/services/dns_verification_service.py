"""
DNS Verification Service

Handles domain ownership verification via DNS TXT records.
Supports both TXT record verification and CNAME verification methods.
"""

import dns.resolver
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Configuration
VERIFICATION_RECORD_PREFIX = "_craftflow-verify"
CNAME_TARGET = "stores.craftflow.store"
DNS_TIMEOUT = 10  # seconds
MAX_ATTEMPTS = 3


@dataclass
class VerificationResult:
    """Result of a domain verification attempt"""
    verified: bool
    method: str
    error: Optional[str] = None
    details: Optional[Dict] = None


def verify_domain_ownership(domain: str, expected_token: str) -> Dict:
    """
    Verify domain ownership by checking DNS records.

    Attempts TXT record verification first, then CNAME verification as fallback.

    Args:
        domain: The domain to verify (e.g., "shop.example.com")
        expected_token: The verification token to look for

    Returns:
        Dict with verification result:
        {
            "verified": bool,
            "method": str,  # "dns_txt" or "dns_cname"
            "error": str or None,
            "details": {
                "txt_found": bool,
                "cname_found": bool,
                "records_found": list
            }
        }
    """
    result = {
        "verified": False,
        "method": None,
        "error": None,
        "details": {
            "txt_found": False,
            "cname_found": False,
            "records_found": []
        }
    }

    # Try TXT record verification first
    txt_result = verify_txt_record(domain, expected_token)
    if txt_result.verified:
        result["verified"] = True
        result["method"] = "dns_txt"
        result["details"]["txt_found"] = True
        result["details"]["records_found"] = txt_result.details.get("records", [])
        logger.info(f"Domain {domain} verified via TXT record")
        return result

    result["details"]["txt_found"] = False
    if txt_result.details:
        result["details"]["records_found"] = txt_result.details.get("records", [])

    # Try CNAME verification as fallback
    cname_result = verify_cname_record(domain)
    if cname_result.verified:
        # CNAME alone is not enough, need TXT too
        result["details"]["cname_found"] = True
        result["error"] = "CNAME record found but TXT verification record is missing. Please add the TXT record."
        logger.warning(f"Domain {domain} has CNAME but missing TXT record")
        return result

    # Neither verification method worked
    result["error"] = txt_result.error or "DNS verification records not found"
    logger.warning(f"Domain {domain} verification failed: {result['error']}")
    return result


def verify_txt_record(domain: str, expected_token: str) -> VerificationResult:
    """
    Verify domain via TXT record.

    Looks for: _craftflow-verify.{domain} TXT record containing the expected token.

    Args:
        domain: The domain to verify
        expected_token: The verification token to look for

    Returns:
        VerificationResult with verification status
    """
    # Parse domain to get subdomain and root
    domain_parts = domain.split('.')

    # Construct the verification record name
    # For shop.example.com -> _craftflow-verify.shop.example.com
    # For example.com -> _craftflow-verify.example.com
    txt_record_name = f"{VERIFICATION_RECORD_PREFIX}.{domain}"

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = DNS_TIMEOUT
        resolver.lifetime = DNS_TIMEOUT

        records = []

        # Try the full verification record name
        try:
            answers = resolver.resolve(txt_record_name, 'TXT')
            for rdata in answers:
                txt_value = str(rdata).strip('"')
                records.append(txt_value)
                if expected_token in txt_value:
                    return VerificationResult(
                        verified=True,
                        method="dns_txt",
                        details={"records": records, "record_name": txt_record_name}
                    )
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            pass

        # Try just _craftflow-verify on the root domain if subdomain
        if len(domain_parts) > 2:
            root_domain = '.'.join(domain_parts[-2:])
            root_txt_name = f"{VERIFICATION_RECORD_PREFIX}.{root_domain}"
            try:
                answers = resolver.resolve(root_txt_name, 'TXT')
                for rdata in answers:
                    txt_value = str(rdata).strip('"')
                    records.append(txt_value)
                    if expected_token in txt_value:
                        return VerificationResult(
                            verified=True,
                            method="dns_txt",
                            details={"records": records, "record_name": root_txt_name}
                        )
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
                pass

        # Records found but token not matching
        if records:
            return VerificationResult(
                verified=False,
                method="dns_txt",
                error=f"TXT records found but verification token not matching",
                details={"records": records}
            )

        return VerificationResult(
            verified=False,
            method="dns_txt",
            error=f"No TXT record found at {txt_record_name}",
            details={"records": []}
        )

    except dns.resolver.Timeout:
        return VerificationResult(
            verified=False,
            method="dns_txt",
            error="DNS query timed out. DNS servers may be slow or unreachable.",
            details={"records": []}
        )
    except Exception as e:
        logger.error(f"DNS TXT verification error for {domain}: {e}")
        return VerificationResult(
            verified=False,
            method="dns_txt",
            error=f"DNS query failed: {str(e)}",
            details={"records": []}
        )


def verify_cname_record(domain: str) -> VerificationResult:
    """
    Verify that domain has CNAME pointing to CraftFlow servers.

    Looks for: {domain} CNAME -> stores.craftflow.store

    Args:
        domain: The domain to verify

    Returns:
        VerificationResult with verification status
    """
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = DNS_TIMEOUT
        resolver.lifetime = DNS_TIMEOUT

        answers = resolver.resolve(domain, 'CNAME')

        for rdata in answers:
            cname_target = str(rdata.target).rstrip('.')
            if CNAME_TARGET in cname_target or cname_target == CNAME_TARGET:
                return VerificationResult(
                    verified=True,
                    method="dns_cname",
                    details={"cname_target": cname_target}
                )

            # Also accept if pointing to any craftflow.store subdomain
            if 'craftflow.store' in cname_target:
                return VerificationResult(
                    verified=True,
                    method="dns_cname",
                    details={"cname_target": cname_target}
                )

        return VerificationResult(
            verified=False,
            method="dns_cname",
            error=f"CNAME record does not point to {CNAME_TARGET}",
            details={"found_target": str(answers[0].target) if answers else None}
        )

    except dns.resolver.NoAnswer:
        # No CNAME record - might have A record instead, which is also valid
        return verify_a_record(domain)
    except dns.resolver.NXDOMAIN:
        return VerificationResult(
            verified=False,
            method="dns_cname",
            error="Domain does not exist in DNS",
            details={}
        )
    except dns.resolver.Timeout:
        return VerificationResult(
            verified=False,
            method="dns_cname",
            error="DNS query timed out",
            details={}
        )
    except Exception as e:
        logger.error(f"DNS CNAME verification error for {domain}: {e}")
        return VerificationResult(
            verified=False,
            method="dns_cname",
            error=f"DNS query failed: {str(e)}",
            details={}
        )


def verify_a_record(domain: str) -> VerificationResult:
    """
    Verify that domain has A record pointing to CraftFlow servers.

    This is a fallback for when CNAME is not used (e.g., root domains).

    Args:
        domain: The domain to verify

    Returns:
        VerificationResult with verification status
    """
    # Define CraftFlow server IPs (these should be configured)
    CRAFTFLOW_IPS = []  # Add actual IPs when known

    if not CRAFTFLOW_IPS:
        # If we don't have IPs configured, we can't verify A records
        return VerificationResult(
            verified=False,
            method="dns_a",
            error="A record verification not configured",
            details={}
        )

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = DNS_TIMEOUT
        resolver.lifetime = DNS_TIMEOUT

        answers = resolver.resolve(domain, 'A')

        for rdata in answers:
            ip = str(rdata)
            if ip in CRAFTFLOW_IPS:
                return VerificationResult(
                    verified=True,
                    method="dns_a",
                    details={"ip": ip}
                )

        return VerificationResult(
            verified=False,
            method="dns_a",
            error="A record does not point to CraftFlow servers",
            details={"found_ips": [str(r) for r in answers]}
        )

    except Exception as e:
        return VerificationResult(
            verified=False,
            method="dns_a",
            error=f"A record verification failed: {str(e)}",
            details={}
        )


def check_domain_propagation(domain: str) -> Dict:
    """
    Check DNS propagation status for a domain.

    Queries multiple DNS servers to check if records have propagated.

    Args:
        domain: The domain to check

    Returns:
        Dict with propagation status from different DNS servers
    """
    # Popular public DNS servers to check
    dns_servers = [
        ("8.8.8.8", "Google"),
        ("1.1.1.1", "Cloudflare"),
        ("208.67.222.222", "OpenDNS"),
        ("9.9.9.9", "Quad9"),
    ]

    results = {}

    for ip, name in dns_servers:
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [ip]
            resolver.timeout = 5
            resolver.lifetime = 5

            # Check for any record type
            try:
                resolver.resolve(domain, 'A')
                results[name] = {"status": "propagated", "ip": ip}
            except dns.resolver.NoAnswer:
                try:
                    resolver.resolve(domain, 'CNAME')
                    results[name] = {"status": "propagated", "ip": ip}
                except:
                    results[name] = {"status": "no_records", "ip": ip}
            except dns.resolver.NXDOMAIN:
                results[name] = {"status": "not_found", "ip": ip}

        except Exception as e:
            results[name] = {"status": "error", "ip": ip, "error": str(e)}

    return {
        "domain": domain,
        "servers_checked": len(dns_servers),
        "results": results,
        "fully_propagated": all(r.get("status") == "propagated" for r in results.values())
    }
