from typing import Annotated


from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BeforeValidator, Field

from schema_components.validators import (
    validate_key_input,
    validate_key_output,
)

type ContactName = Annotated[
    str,
    Field(
        title='Name',
        description='A uniquely identifying name for this contact.',
        max_length=255,
        min_length=1,
    ),
]

type Base64Key = Annotated[
    str,
    Field(
        title='Base64-Encoded Key',
        description='The Base64 representation of a 32-byte value.',
        max_length=44,
        min_length=44,
    ),
    BeforeValidator(validate_key_input),
]

type VerificationKey = Annotated[
    Ed25519PublicKey,
    BeforeValidator(lambda x: validate_key_output(x, Ed25519PublicKey)),
]