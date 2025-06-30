from cryptography.fernet import Fernet
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import Contact
from database.schemas.outputs import ContactOutputSchema

def get_contacts(engine: Engine) -> list[ContactOutputSchema]:
    query = (
        select(Contact)
        .order_by(Contact.name)
    )
    with Session(engine) as session:
        contacts = session.scalars(query)
        return [ContactOutputSchema.model_validate(x) for x in contacts]
    
def get_fernet_key(engine: Engine, contact_id: int) -> Fernet:
    """Retrieve the latest Fernet key available for a contact."""
    with Session(engine) as session:
        obj = session.get(Contact, contact_id).fernet_keys

    
def process_message(
        engine: Engine,
        contact: ContactOutputSchema,
        plaintext: str,
    ):
    """Encrypt a message and prepare it for posting."""

