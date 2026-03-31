import subprocess


def _run(cmd: list[str], stdin: str | None = None) -> str:
    result = subprocess.run(
        cmd,
        input=stdin,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command {cmd} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def generate_private_key() -> str:
    return _run(["wg", "genkey"])


def derive_public_key(private_key: str) -> str:
    return _run(["wg", "pubkey"], stdin=private_key)


def generate_preshared_key() -> str:
    return _run(["wg", "genpsk"])


def generate_keypair() -> tuple[str, str]:
    private = generate_private_key()
    public = derive_public_key(private)
    return private, public


def generate_keypair_python() -> tuple[str, str]:
    """Fallback key generation using cryptography library (no wg binary needed)."""
    import base64
    import os

    # X25519 private key: 32 random bytes with clamping
    private_bytes = bytearray(os.urandom(32))
    private_bytes[0] &= 248
    private_bytes[31] &= 127
    private_bytes[31] |= 64

    try:
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

        private_key = X25519PrivateKey.from_private_bytes(bytes(private_bytes))
        public_bytes = private_key.public_key().public_bytes_raw()
        return (
            base64.b64encode(bytes(private_bytes)).decode(),
            base64.b64encode(public_bytes).decode(),
        )
    except ImportError:
        raise RuntimeError(
            "Either 'wg' binary or 'cryptography' package is required for key generation"
        )


def safe_generate_keypair() -> tuple[str, str]:
    """Generate keypair using wg binary, falling back to Python if unavailable."""
    try:
        return generate_keypair()
    except (FileNotFoundError, RuntimeError):
        return generate_keypair_python()
