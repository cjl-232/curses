from pydantic import BaseModel

from schema_components.types import Base64Key, Base64Signature

class _BaseRequestSchema(BaseModel):
    user_public_key: Base64Key

class _BasePostRequestSchema(_BaseRequestSchema):
    recipient_public_key: Base64Key
    signature: Base64Signature

class PostExchangeKeyRequestSchema(_BasePostRequestSchema):
    exchange_key: Base64Key

class PostMessageRequestSchema(_BasePostRequestSchema):
    encrypted_text: str

class FetchRequestSchema(_BaseRequestSchema):
    pass