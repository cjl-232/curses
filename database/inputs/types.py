from typing import Annotated

from pydantic import BeforeValidator, Field

from database.inputs.validators import validate_key

type ContactName = Annotated[
    str,
    Field(
        title='Name',
        description='A uniquely identifying name for this contact.',
        max_length=255,
        min_length=1,
    ),
]

type Key = Annotated[
    str,
    Field(
        title='Base64-Encoded Key',
        description='The Base64 representation of a 32-byte value.',
        max_length=44,
        min_length=44,
    ),
    BeforeValidator(validate_key),
]