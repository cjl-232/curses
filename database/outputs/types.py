from typing import Annotated

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BeforeValidator

from database.outputs.validators import validate_key

type VerificationKey = Annotated[
    Ed25519PublicKey,
    BeforeValidator(lambda x: validate_key(x, Ed25519PublicKey)),
]