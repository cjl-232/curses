from base64 import urlsafe_b64decode, urlsafe_b64encode

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)

type _PrivateKeyType = type[Ed25519PrivateKey] | type[X25519PrivateKey]
type _PublicKeyType = type[Ed25519PublicKey] | type[X25519PublicKey]

def validate_key(
        value: str,
        key_type: _PrivateKeyType | _PublicKeyType | type[Fernet]
    ):
    raw_bytes = urlsafe_b64decode(value)
    if issubclass(key_type, (Ed25519PrivateKey, X25519PrivateKey)):
        return key_type.from_private_bytes(raw_bytes)
    elif issubclass(key_type, (Ed25519PublicKey, X25519PublicKey)):
        return key_type.from_public_bytes(raw_bytes)
    else:
        return Fernet(urlsafe_b64encode(raw_bytes))