from pydantic import BaseModel

from database.inputs.types import ContactName, Key

class ContactInputSchema(BaseModel):
    name: ContactName
    public_key: Key
