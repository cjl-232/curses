from argparse import ArgumentParser

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

class LaunchParser(ArgumentParser):
    def __init__(self) -> None:
        super().__init__(description=_DESCRIPTION)
        group = self.add_mutually_exclusive_group(required=True)
        group.add_argument('--hex', help=_HEX_HELP)
        group.add_argument('--base64', help=_BASE64_HELP)
        group.add_argument('--pem', help=_PEM_HELP)
        group.add_argument('--der', help=_DER_HELP)
        self.add_argument('--password', help=_PASSWORD_HELP)

if __name__ == '__main__':
    parser = LaunchParser()
    args = parser.parse_args()
    print(args)