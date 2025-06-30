from pydantic import BaseModel

from schema_components.types import Base64Key, ContactName

class ContactInputSchema(BaseModel):
    name: ContactName
    verification_key: Base64Key
