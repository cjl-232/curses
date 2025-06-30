import httpx

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import Contact
from exceptions import FailedRequest
from server.schemas.requests import FetchRequestSchema
from server.schemas.responses import FetchResponseSchema
from settings import settings

def fetch_data(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
        client: httpx.Client,
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