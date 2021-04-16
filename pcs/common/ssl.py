import datetime

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_key(length: int = 3072) -> rsa.RSAPrivateKeyWithSerialization:
    return rsa.generate_private_key(
        public_exponent=65537, key_size=length, backend=default_backend()
    )


def generate_cert(key: rsa.RSAPrivateKey, server_name: str) -> x509.Certificate:
    now = datetime.datetime.utcnow()
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "MN"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Minneapolis"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "pcsd"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "pcsd"),
            x509.NameAttribute(NameOID.COMMON_NAME, server_name),
        ]
    )
    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(int(now.timestamp() * 1000))
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=3650))
        .sign(key, hashes.SHA256(), default_backend())
    )


def dump_cert(certificate: x509.Certificate) -> bytes:
    return certificate.public_bytes(serialization.Encoding.PEM)


def dump_key(key: rsa.RSAPrivateKeyWithSerialization) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
