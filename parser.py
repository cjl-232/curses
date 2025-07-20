import binascii

from argparse import ArgumentParser
from base64 import urlsafe_b64decode
from enum import auto, Enum
from functools import cached_property

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

_DESCRIPTION = (
    'Launch an instance of the client with a specified private key. Exactly '
    'one of --hex, --base64, --pem, and --der must be provided. If --pem or '
    '--der is provided and the value represents an encrypted file, the '
    'decryption password should also be provided via the --password argument.'
)

_HEX_HELP = 'Hex-encoded 32-byte value (64 characters)'

_BASE64_HELP = 'Base64-encoded 32-byte value (44 characters)'

_PEM_HELP = 'Path to a file containing a PEM-encoded Ed25519 private key'

_DER_HELP = 'Path to a file containing a DER-encoded Ed25519 private key'

_PASSWORD_HELP = 'Password for a PEM or DER-encoded Ed25519 private key'

def _hex_to_key(value: str) -> Ed25519PrivateKey:
    try:
        raw_bytes = bytes.fromhex(value)
    except ValueError:
        raise ValueError('value is not valid hexadecimal')
    if len(raw_bytes) != 32:
        raise ValueError('value does not represent 32 raw bytes')
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(value))

def _base64_to_key(value: str) -> Ed25519PrivateKey:
    try:
        raw_bytes = urlsafe_b64decode(value)
    except binascii.Error:
        raise ValueError('value is not valid Base64')
    if len(raw_bytes) != 32:
        raise ValueError('value does not represent 32 raw bytes')
    return Ed25519PrivateKey.from_private_bytes(raw_bytes)

class _Encoding(Enum):
    PEM = auto()
    DER = auto()

def _file_to_key(
        value: str,
        password: str | None,
        encoding: _Encoding,
    ) -> Ed25519PrivateKey:
    with open(value, 'rb') as file:
        data = file.read()
    match(encoding):
        case _Encoding.PEM:
            load_function = serialization.load_pem_private_key
        case _Encoding.DER:
            load_function = serialization.load_der_private_key
    try:
        key = load_function(data, None)
    except TypeError as e:
        if password is not None:
            key = load_function(data, password.encode())
        else:
            raise e
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError(f'File represents a non-Ed25519 private key')
    return key

class ClientArgumentParser(ArgumentParser):
    def __init__(self) -> None:
        super().__init__(description=_DESCRIPTION)
        group = self.add_mutually_exclusive_group(required=True)
        group.add_argument('--hex', help=_HEX_HELP)
        group.add_argument('--base64', help=_BASE64_HELP)
        group.add_argument('--pem', help=_PEM_HELP)
        group.add_argument('--der', help=_DER_HELP)
        self.add_argument('--password', help=_PASSWORD_HELP)

    @cached_property
    def signature_key(self) -> Ed25519PrivateKey:
        args = self.parse_args()
        if args.hex is not None:
            try:
                return _hex_to_key(args.hex)
            except Exception as e:
                raise ValueError(f'--hex error: {e}')
        elif args.base64 is not None:
            try:
                return _base64_to_key(args.base64)
            except Exception as e:
                raise ValueError(f'--base64 error: {e}')
        elif args.pem is not None:
            try:
                return _file_to_key(args.pem, args.password, _Encoding.PEM)
            except Exception as e:
                raise ValueError(f'--pem error: {e}')
        elif args.der is not None:
            try:
                return _file_to_key(args.der, args.password, _Encoding.DER)
            except Exception as e:
                raise ValueError(f'--der error: {e}')
        assert False  # Unreachable for unmodified parse_args


if __name__ == '__main__':
    parser = ClientArgumentParser()
    key = parser.signature_key
    print(parser.signature_key.private_bytes_raw())
