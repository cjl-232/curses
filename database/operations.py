from base64 import urlsafe_b64encode
from functools import cache

from cryptography.fernet import Fernet
from sqlalchemy import Engine, exists, select
from sqlalchemy.orm import Session

from database.models import Contact, FernetKey, Message, MessageType
from database.schemas.inputs import ContactInputSchema, MessageInputSchema
from database.schemas.outputs import ContactOutputSchema
from exceptions import MissingFernetKey
from server.schemas.responses import FetchResponseSchema

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
            

def get_contacts(engine: Engine) -> list[ContactOutputSchema]:
    query = (
        select(Contact)
        .order_by(Contact.name)
    )
    with Session(engine) as session:
        contacts = session.scalars(query)
        return [ContactOutputSchema.model_validate(x) for x in contacts]
    
def get_fernet_key(engine: Engine, contact: ContactOutputSchema) -> Fernet:
    """Retrieve the latest Fernet key available for a contact."""
    query = (
        select(FernetKey.encoded_bytes)
        .where(FernetKey.contact_id == contact.id)
        .order_by(FernetKey.timestamp.desc())
    )
    with Session(engine) as session:
        encoded_bytes = session.scalar(query)
        if encoded_bytes is None:
            msg = f'No shared key exists for {contact.name}.'
            raise MissingFernetKey(msg)
        return Fernet(encoded_bytes)

    
def store_message(
        engine: Engine,
        contact: ContactOutputSchema,
        plaintext: str,
    ):
    """Encrypt a message and prepare it for posting."""

def store_fetched_data(engine: Engine, response: FetchResponseSchema):
    # Cached functions are used for data retrieval.
    @cache
    def get_contact_id(key: str) -> int | None:
        query = select(Contact.id).where(Contact.verification_key == key)
        with Session(engine) as session:
            return session.scalar(query)
    @cache
    def get_fernet_keys(contact_id: int) -> list[Fernet]:
        query = (
            select(FernetKey.encoded_bytes)
            .where(FernetKey.contact_id == contact_id)
            .order_by(FernetKey.timestamp.desc())
        )
        with Session(engine) as session:
            return [Fernet(x) for x in session.scalars(query)]
    @cache
    def nonce_exists(nonce: str) -> bool:
        query = exists().where(Message.nonce == nonce).select()
        with Session(engine) as session:
            return bool(session.scalar(query))
    # Iterate over fetched messages and keys.
    with Session(engine) as session:
        for message in response.data.messages:
            # Check each message is valid, new, and from a registered contact.
            if not message.is_valid:
                continue
            elif get_contact_id(message.sender_public_key_b64) is None:
                continue
            elif not nonce_exists(message.nonce):
                continue
            contact_id = get_contact_id(message.sender_public_key_b64)
            # Attempt to decrypt each message.
            text = ''
            for fernet_key in get_fernet_keys(contact_id):
                try:
                    text = fernet_key.decrypt(message.encrypted_text).decode()
                    break
                except Exception:
                    pass
            if not text:
                continue
            # Add decrypted messages to the database.
            input = MessageInputSchema.model_validate({
                'text': text,
                'contact_id': contact_id,
                'message_type': MessageType.RECEIVED,
                'timestamp': message.timestamp,
                'nonce': message.nonce,
            })
            session.add(Message(**input.model_dump()))
        
        for exchange_key in response.data.exchange_keys:
            print(exchange_key)
        session.commit()



