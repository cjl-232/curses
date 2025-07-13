from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timezone
from typing import cast

from cryptography.fernet import Fernet
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
type _KeyInputType = str | _BytesLike | _PrivateKey | _PublicKey
type _PrivateKeyType = type[Ed25519PrivateKey] | type[X25519PrivateKey]
type _PublicKeyType = type[Ed25519PublicKey] | type[X25519PublicKey]


def validate_key_input(value: _KeyInputType) -> str:
    if isinstance(value, str):
        raw_bytes = urlsafe_b64decode(value)
        if len(raw_bytes) == 32:
            return urlsafe_b64encode(raw_bytes).decode()
        raise ValueError('Value must have an unencoded length of 32 bytes.')
    elif isinstance(value, (bytes, bytearray, memoryview)):
        if len(value) == 32:
            return urlsafe_b64encode(value).decode()
        raise ValueError('Value must have an unencoded length of 32 bytes.')
    elif isinstance(value, (Ed25519PrivateKey, X25519PrivateKey)):
        return urlsafe_b64encode(value.private_bytes_raw()).decode()
    else:
        return urlsafe_b64encode(value.public_bytes_raw()).decode()


def validate_key_list_input(value: list[_KeyInputType]) -> list[str]:
    return [validate_key_input(x) for x in value]

    
def validate_signature_input(value: str | _BytesLike) -> str:
    if isinstance(value, str):
        value = urlsafe_b64decode(value)
    if len(value) != 64:
        raise ValueError('Value must have an unencoded length of 64 bytes.')
    return urlsafe_b64encode(value).decode()


def validate_timestamp_input(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc)


def validate_key_output[T: _PrivateKey | _PublicKey | Fernet](
        value: str,
        key_type: type[T],
    ) -> T:
    raw_bytes = urlsafe_b64decode(value)
    if issubclass(key_type, (Ed25519PrivateKey, X25519PrivateKey)):
        return cast(T, key_type.from_private_bytes(raw_bytes))
    elif issubclass(key_type, (Ed25519PublicKey, X25519PublicKey)):
        return cast(T, key_type.from_public_bytes(raw_bytes))
    else:
        return key_type(raw_bytes)







    
def validate_signature_output(value: str) -> bytes:
    raw_bytes = urlsafe_b64decode(value)
    if len(raw_bytes) != 64:
        raise ValueError('Value must have an unencoded length of 64 bytes.')
    return raw_bytes