from base64 import urlsafe_b64encode
from functools import lru_cache

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from sqlalchemy import Engine, exists, select
from sqlalchemy.orm import Session

from database.models import (
    Contact,
    FernetKey,
    Message,
    MessageType,
    ReceivedExchangeKey,
    SentExchangeKey,
)
from database.schemas.inputs import (
    ContactInputSchema,
    MessageInputSchema,
    SentKeyInputSchema,
)
from database.schemas.outputs import (
    BaseContactOutputSchema,
    ContactOutputSchema,
    ReceivedKeyOutputSchema,
    SentKeyOutputSchema,
)
from server.schemas.responses import (
    FetchResponseExchangeKey,
    FetchResponseMessage,
    FetchResponseSchema,
    PostMessageResponseSchema
)

def add_contact(engine: Engine, contact: ContactInputSchema):
    with Session(engine) as session:
        session.add(Contact(**contact.model_dump()))
        session.commit()


def get_contact(
        engine: Engine,
        verification_key_bytes: bytes,
    ) -> ContactOutputSchema | None:
    b64_key_bytes = urlsafe_b64encode(verification_key_bytes)
    query = (
        select(Contact)
        .where(Contact.verification_key == b64_key_bytes.decode())
    )
    with Session(engine) as session:
        contact = session.scalar(query)
        if contact is not None:
            return ContactOutputSchema.model_validate(contact)
        return None


def get_contact_keys(engine: Engine) -> list[str]:
    with Session(engine) as session:
        return list(session.scalars(select(Contact.verification_key)))


def get_contacts(engine: Engine) -> list[BaseContactOutputSchema]:
    query = (
        select(Contact)
        .order_by(Contact.name)
    )
    with Session(engine) as session:
        contacts = session.scalars(query)
        return [BaseContactOutputSchema.model_validate(x) for x in contacts]


def get_unmatched_keys(engine: Engine) -> list[ReceivedKeyOutputSchema]:
    """Return all received keys that have not yet been responded to."""
    query = (
        select(ReceivedExchangeKey)
        .where(ReceivedExchangeKey.matched == False)
    )
    with Session(engine) as session:
        keys = session.scalars(query)
        return [ReceivedKeyOutputSchema.model_validate(x) for x in keys]


@lru_cache(maxsize=256)
def _get_contact_from_key(
    session: Session,
    public_key: str,
) -> ContactOutputSchema | None:
    """Internal function to identify contacts from response data."""
    contact = session.scalar((
        select(Contact)
        .where(Contact.verification_key == public_key)
    ))
    if contact is not None:
        return ContactOutputSchema.model_validate(contact)
    return None


def _get_initial_key(
    session: Session,
    encoded_public_bytes: str,
) -> SentKeyOutputSchema | None:
    """Identifies a previously sent key from response data. Not cacheable."""
    sent_key = session.scalar((
        select(SentExchangeKey)
        .where(SentExchangeKey.encoded_public_bytes == encoded_public_bytes)
    ))
    if sent_key is not None:
        return SentKeyOutputSchema.model_validate(sent_key)
    return None


def _received_key_exists(session: Session, key: str) -> bool:
    query = exists().where(ReceivedExchangeKey.encoded_bytes == key).select()
    return bool(session.scalar(query))


def _received_message_exists(session: Session, nonce: str) -> bool:
    query = exists().where(Message.nonce == nonce).select()
    return bool(session.scalar(query))


def _handle_exchange_key_element(
        session: Session,
        element: FetchResponseExchangeKey,
    ) -> None:
    if not element.is_valid:
        return
    elif _received_key_exists(session, element.exchange_key_b64):
        return
    contact = _get_contact_from_key(session, element.sender_key_b64)
    if contact is None:
        return
    if element.initial_key_b64 is not None:
        initial_key = _get_initial_key(session, element.initial_key_b64)
        if initial_key is None or initial_key.contact.id != contact.id:
            return
        shared_secret = initial_key.private_key.exchange(element.exchange_key)
        session.add(
            FernetKey(
                contact_id=contact.id,
                encoded_bytes=urlsafe_b64encode(shared_secret).decode(),
                timestamp=element.timestamp,
            )
        )
        session.add(
            ReceivedExchangeKey(
                encoded_bytes=element.exchange_key_b64,
                matched=True,
                contact_id=contact.id,
            ),
        )
        session.delete(session.get(SentExchangeKey, initial_key.id))
    else:
        session.add(
            ReceivedExchangeKey(
                encoded_bytes=element.exchange_key_b64,
                matched=False,
                contact_id=contact.id,
            ),
        )


def _handle_message_element(
        session: Session,
        element: FetchResponseMessage,
    ) -> None:
    if not element.is_valid:
        return
    elif _received_message_exists(session, element.nonce):
        return
    contact = _get_contact_from_key(session, element.sender_key_b64)
    if contact is None:
        return
    plaintext = ''
    for fernet_key in contact.fernet_keys:
        try:
            plaintext = fernet_key.key.decrypt(element.encrypted_text).decode()
            break
        except Exception:
            pass
    if plaintext:
        session.add(
            Message(
                text=plaintext,
                contact_id=contact.id,
                message_type=MessageType.RECEIVED,
                timestamp=element.timestamp,
                nonce=element.nonce,
            ),
        )


def store_fetched_data(engine: Engine, response: FetchResponseSchema) -> None:
    """Stores the data from a successful fetch request response."""
    # Use an initial session for key exchange.
    with Session(engine) as session:
        for exchange_key in response.data.exchange_keys:
            _handle_exchange_key_element(session, exchange_key)
        session.commit()
    # Use a second session for messages, ensuring fernet keys are accessible.
    with Session(engine) as session:
        for message in response.data.messages:
            _handle_message_element(session, message)
        session.commit()


def store_posted_exchange_key(
        engine: Engine,
        contact_id: int,
        private_exchange_key: X25519PrivateKey,
    ):
    sent_key_input = SentKeyInputSchema.model_validate({
        'encoded_private_bytes': private_exchange_key,
        'encoded_public_bytes': private_exchange_key.public_key(),
        'contact_id': contact_id,
    })
    with Session(engine) as session:
        session.add(SentExchangeKey(**sent_key_input.model_dump()))
        session.commit()

def store_posted_message(
        engine: Engine,
        plaintext: str,
        contact_id: int,
        response: PostMessageResponseSchema,
    ):
    input = MessageInputSchema.model_validate({
        'text': plaintext,
        'contact_id': contact_id,
        'timestamp': response.data.timestamp,
        'nonce': response.data.nonce,
        'message_type': MessageType.SENT,
    })
    with Session(engine) as session:
        session.add(Message(**input.model_dump()))
        session.commit()