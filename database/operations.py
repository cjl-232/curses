from base64 import urlsafe_b64encode
from functools import cache

from cryptography.fernet import Fernet
from sqlalchemy import Engine, exists, select
from sqlalchemy.orm import Session

from database.models import Contact, FernetKey, Message, MessageType
from database.schemas.inputs import MessageInputSchema
from database.schemas.outputs import ContactOutputSchema
from exceptions import MissingFernetKey
from server.schemas.responses import FetchResponseSchema

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

# TODO Need to uncache nones when adding as a contact...
    
# TODO completely clean
def store_fetched_data(
        engine: Engine,
        response: FetchResponseSchema,
    ):
    @cache
    def get_contact_id(raw_key_bytes: bytes):
        b64_key = urlsafe_b64encode(raw_key_bytes).decode()
        query = (
            select(Contact.id)
            .where(Contact.verification_key == b64_key)
        )
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
    with Session(engine) as session:
        for message in response.data.messages:
            if not message.is_valid:
                continue
            sender_key_bytes = message.sender_public_key.public_bytes_raw()
            contact_id = get_contact_id(sender_key_bytes)
            if contact_id is None:
                continue
            text = None
            for fernet_key in get_fernet_keys(contact_id):
                try:
                    text = fernet_key.decrypt(message.encrypted_text).decode()
                    break
                except:
                    pass
            if not text:
                continue
            query = (
                exists()
                .where(Message.nonce == message.nonce)
                .select()
            )
            if session.scalar(query):
                continue
            input = MessageInputSchema.model_validate({
                'text': text,
                'contact_id': contact_id,
                'message_type': MessageType.RECEIVED,
                'timestamp': message.timestamp,
                'nonce': message.nonce,
            })
            session.add(Message(**input.model_dump()))
        
        for exchange_key in response.data.exchange_keys:
            pass
        session.commit()



