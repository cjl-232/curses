from base64 import urlsafe_b64decode, urlsafe_b64encode

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)

type _BytesLike = bytes | bytearray | memoryview
type _PrivateKey = Ed25519PrivateKey | X25519PrivateKey
type _PublicKey = Ed25519PublicKey | X25519PublicKey

def validate_key(value: str | _BytesLike | _PrivateKey | _PublicKey) -> str:
    if isinstance(value, (str, bytes, bytearray, memoryview)):
        raw_bytes = urlsafe_b64decode(value)
        if len(raw_bytes) == 32:
            return urlsafe_b64encode(raw_bytes).decode()
        raise ValueError('Value must have an unencoded length of 32 bytes.')
    elif isinstance(value, (Ed25519PrivateKey, X25519PrivateKey)):
        return urlsafe_b64decode(value.private_bytes_raw()).decode()
    else:
        return urlsafe_b64decode(value.public_bytes_raw()).decode()