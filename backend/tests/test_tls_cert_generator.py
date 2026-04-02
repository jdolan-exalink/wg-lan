"""
Tests for TLS certificate generation and configuration.
"""
import os
import tempfile
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import serialization

from app.utils.tls_cert_generator import generate_self_signed_cert, ensure_certificates_exist


class TestTLSCertGenerator:
    """Test TLS certificate generation functionality."""
    
    def test_generate_self_signed_cert(self):
        """Test that a self-signed certificate is generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cert_path = os.path.join(tmpdir, "test.crt")
            key_path = os.path.join(tmpdir, "test.key")
            
            result_cert, result_key = generate_self_signed_cert(
                cert_path=cert_path,
                key_path=key_path,
                country="AR",
                state="Buenos Aires",
                locality="CABA",
                organization="Test Org",
                common_name="test.local",
                days_valid=365,
            )
            
            # Verify files were created
            assert Path(result_cert).exists()
            assert Path(result_key).exists()
            
            # Verify certificate content
            with open(result_cert, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())
            
            # Check subject attributes
            subject = cert.subject
            assert subject.get_attributes_for_oid(x509.oid.NameOID.COUNTRY_NAME)[0].value == "AR"
            assert subject.get_attributes_for_oid(x509.oid.NameOID.STATE_OR_PROVINCE_NAME)[0].value == "Buenos Aires"
            assert subject.get_attributes_for_oid(x509.oid.NameOID.LOCALITY_NAME)[0].value == "CABA"
            assert subject.get_attributes_for_oid(x509.oid.NameOID.ORGANIZATION_NAME)[0].value == "Test Org"
            assert subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value == "test.local"
            
            # Verify key file
            with open(result_key, "rb") as f:
                key = serialization.load_pem_private_key(f.read(), password=None)
            assert key.key_size == 2048
            
            # Verify permissions
            key_stat = os.stat(result_key)
            assert oct(key_stat.st_mode)[-3:] == "600"
    
    def test_ensure_certificates_exist_creates_new(self):
        """Test that certificates are created when they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cert_path = os.path.join(tmpdir, "new.crt")
            key_path = os.path.join(tmpdir, "new.key")
            
            result_cert, result_key = ensure_certificates_exist(
                cert_path=cert_path,
                key_path=key_path,
            )
            
            assert Path(result_cert).exists()
            assert Path(result_key).exists()
    
    def test_ensure_certificates_exist_skips_existing(self):
        """Test that existing certificates are not overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cert_path = os.path.join(tmpdir, "existing.crt")
            key_path = os.path.join(tmpdir, "existing.key")
            
            # Create initial certificates
            generate_self_signed_cert(
                cert_path=cert_path,
                key_path=key_path,
                common_name="original.local",
            )
            
            # Read original cert
            with open(cert_path, "rb") as f:
                original_cert_data = f.read()
            
            # Try to ensure certificates exist (should not overwrite)
            result_cert, result_key = ensure_certificates_exist(
                cert_path=cert_path,
                key_path=key_path,
                common_name="new.local",
            )
            
            # Verify cert was not overwritten
            with open(cert_path, "rb") as f:
                new_cert_data = f.read()
            
            assert original_cert_data == new_cert_data
    
    def test_certificate_has_san_extension(self):
        """Test that generated certificate has Subject Alternative Names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cert_path = os.path.join(tmpdir, "san.crt")
            key_path = os.path.join(tmpdir, "san.key")
            
            generate_self_signed_cert(
                cert_path=cert_path,
                key_path=key_path,
                common_name="san.local",
            )
            
            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())
            
            # Get SAN extension
            san_ext = cert.extensions.get_extension_for_class(
                x509.SubjectAlternativeName
            )
            
            san_names = san_ext.value
            assert x509.DNSName("san.local") in san_names
            assert x509.DNSName("localhost") in san_names
    
    def test_certificate_validity_period(self):
        """Test that certificate has correct validity period."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cert_path = os.path.join(tmpdir, "validity.crt")
            key_path = os.path.join(tmpdir, "validity.key")
            
            days = 730  # 2 years
            generate_self_signed_cert(
                cert_path=cert_path,
                key_path=key_path,
                days_valid=days,
            )
            
            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())
            
            # Check validity period is approximately correct
            delta = cert.not_valid_after_utc - cert.not_valid_before_utc
            assert delta.days >= days - 1  # Allow 1 day tolerance
