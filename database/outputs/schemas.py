from pydantic import BaseModel

from database.outputs.types import VerificationKey

class ContactOutputSchema(BaseModel):
    id: int
    name: str
    verification_key: VerificationKey

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True