from typing import Any

import httpx

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
from pydantic import BaseModel

from server.schemas.requests import (
    FetchRequestSchema,
    PostExchangeKeyRequestSchema,
    PostMessageRequestSchema,
)
from server.schemas.responses import (
    FetchResponseSchema,
    PostExchangeKeyResponseSchema,
    PostMessageResponseSchema,
)
from settings import settings

def _process_request[T: BaseModel, U: BaseModel](
        client: httpx.Client,
        method: str,
        url: str,
        request_model: type[T],
        response_model: type[U],
        **kwargs: Any,
    ) -> U:
    request = request_model.model_validate(kwargs)
    response = client.request(method, url, json=request.model_dump())
    response.raise_for_status()
    return response_model.model_validate(response.json())

def fetch_data(
        client: httpx.Client,
        signature_key: Ed25519PrivateKey,
        contact_keys: list[str],
    ) -> FetchResponseSchema:
    """Fetch all data stored on the server that is addressed to the user."""
    return _process_request(
        client=client,
        method='POST',
        url=settings.server.url.fetch_data_url,
        request_model=FetchRequestSchema,
        response_model=FetchResponseSchema,
        public_key=signature_key.public_key(),
        sender_keys=contact_keys,
    )

def post_exchange_key(
        client: httpx.Client,
        signature_key: Ed25519PrivateKey,
        recipient_public_key: Ed25519PublicKey,
        exchange_key: X25519PublicKey,
        initial_exchange_key: X25519PublicKey | None = None,
    ) -> PostExchangeKeyResponseSchema:
    """Post a single exchange key to the server."""
    return _process_request(
        client=client,
        method='POST',
        url=settings.server.url.post_exchange_key_url,
        request_model=PostExchangeKeyRequestSchema,
        response_model=PostExchangeKeyResponseSchema,
        public_key=signature_key.public_key(),
        recipient_public_key=recipient_public_key,
        transmitted_exchange_key=exchange_key,
        signature=signature_key.sign(exchange_key.public_bytes_raw()),
        initial_exchange_key=initial_exchange_key,
    )

def post_message(
        client: httpx.Client,
        signature_key: Ed25519PrivateKey,
        recipient_public_key: Ed25519PublicKey,
        encrypted_text: bytes,
    ) -> PostMessageResponseSchema:
    """Post a single message to the server."""
    return _process_request(
        client=client,
        method='POST',
        url=settings.server.url.post_message_url,
        request_model=PostMessageRequestSchema,
        response_model=PostMessageResponseSchema,
        public_key=signature_key.public_key(),
        recipient_public_key=recipient_public_key,
        encrypted_text=encrypted_text,
        signature=signature_key.sign(encrypted_text),
    )
