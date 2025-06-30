from cryptography.fernet import Fernet
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import Contact, FernetKey
from database.schemas.outputs import ContactOutputSchema
from exceptions import MissingFernetKey

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

