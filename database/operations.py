from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import Contact
from database.outputs.schemas import ContactOutputSchema

def get_contacts(engine: Engine) -> list[ContactOutputSchema]:
    query = (
        select(Contact)
        .order_by(Contact.name)
    )
    with Session(engine) as session:
        contacts = session.scalars(query)
        return [ContactOutputSchema.model_validate(x) for x in contacts]
