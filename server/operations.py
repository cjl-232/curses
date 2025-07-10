import httpx

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import Contact
from exceptions import FailedRequest
from server.schemas.requests import (
    FetchRequestSchema,
    PostExchangeKeyRequestSchema,
)
from server.schemas.responses import (
    FetchResponseSchema,
    PostExchangeKeyResponseSchema,
)
from settings import settings

def fetch_data(
        engine: Engine,
        client: httpx.Client,
        signature_key: Ed25519PrivateKey,
    ) -> FetchResponseSchema | None:
    """Fetch all data stored on the server that is addressed to the user."""
    with Session(engine) as session:
        request = FetchRequestSchema.model_validate({
            'public_key': signature_key.public_key(),
            'sender_keys': session.scalars(select(Contact.verification_key)),
        })
    if not request.sender_keys:
        return None
    raw_response = client.post(
        url=settings.server.url.fetch_data_url,
        json=request.model_dump(),
    )
    if not raw_response.is_success:
        raise FailedRequest('Fetch request failed.', raw_response)
    return FetchResponseSchema.model_validate(raw_response.json())

def post_exchange_key(
        client: httpx.Client,
        signature_key: Ed25519PrivateKey,
        recipient_public_key: Ed25519PublicKey,
        exchange_key: X25519PublicKey,
        initial_exchange_key: X25519PublicKey | None = None,
    ) -> PostExchangeKeyResponseSchema:
    request = PostExchangeKeyRequestSchema.model_validate({
        'public_key': signature_key.public_key(),
        'recipient_public_key': recipient_public_key,
        'transmitted_exchange_key': exchange_key,
        'signature': signature_key.sign(exchange_key.public_bytes_raw()),
        'initial_exchange_key': initial_exchange_key,
    })
    raw_response = client.post(
        url=settings.server.url.post_exchange_key_url,
        json=request.model_dump(),
    )
    if not raw_response.is_success:
        raise FailedRequest('Post exchange key request failed.', raw_response)
    return PostExchangeKeyResponseSchema.model_validate(raw_response.json())