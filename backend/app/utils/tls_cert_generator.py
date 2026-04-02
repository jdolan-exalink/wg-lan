"""
Utility for generating self-signed TLS certificates.
Used when TLS is enabled but no certificates exist.
"""
import datetime
import os
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_self_signed_cert(
    cert_path: str,
    key_path: str,
    country: str = "US",
    state: str = "California",
    locality: str = "San Francisco",
    organization: str = "NetLoom",
    common_name: str = "netloom.local",
    days_valid: int = 3650,
) -> tuple[str, str]:
    """
    Generate a self-signed TLS certificate and private key.
    
    Args:
        cert_path: Path to save the certificate (PEM format)
        key_path: Path to save the private key (PEM format)
        country: Country name (C)
        state: State or province name (ST)
        locality: Locality name (L)
        organization: Organization name (O)
        common_name: Common name (CN)
        days_valid: Number of days the certificate is valid
        
    Returns:
        Tuple of (cert_path, key_path)
    """
    # Create directories if they don't exist
    Path(cert_path).parent.mkdir(parents=True, exist_ok=True)
    Path(key_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Build certificate subject and issuer
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
        x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    # Build certificate
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days_valid)
        )
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(common_name),
                x509.DNSName("localhost"),
                x509.IPAddress(__import__("ipaddress").ip_address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )
    
    # Write private key
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    
    # Write certificate
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    # Set restrictive permissions on key file
    os.chmod(key_path, 0o600)
    os.chmod(cert_path, 0o644)
    
    return cert_path, key_path


def ensure_certificates_exist(
    cert_path: str,
    key_path: str,
    country: str = "US",
    state: str = "California",
    locality: str = "San Francisco",
    organization: str = "NetLoom",
    common_name: str = "netloom.local",
    days_valid: int = 3650,
) -> tuple[str, str]:
    """
    Ensure TLS certificates exist. Generate them if they don't.
    
    Args:
        cert_path: Path to the certificate file
        key_path: Path to the private key file
        country: Country name (C)
        state: State or province name (ST)
        locality: Locality name (L)
        organization: Organization name (O)
        common_name: Common name (CN)
        days_valid: Number of days the certificate is valid
        
    Returns:
        Tuple of (cert_path, key_path)
    """
    if not Path(cert_path).exists() or not Path(key_path).exists():
        print(f"==> TLS certificates not found, generating self-signed certificate...")
        print(f"    Certificate: {cert_path}")
        print(f"    Key: {key_path}")
        return generate_self_signed_cert(
            cert_path=cert_path,
            key_path=key_path,
            country=country,
            state=state,
            locality=locality,
            organization=organization,
            common_name=common_name,
            days_valid=days_valid,
        )
    else:
        print(f"==> TLS certificates found at {cert_path} and {key_path}")
        return cert_path, key_path
