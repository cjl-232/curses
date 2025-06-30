from datetime import datetime

from pydantic import BaseModel

from database.models import MessageType
from schema_components.types import VerificationKey

class ContactOutputSchema(BaseModel):
    id: int
    name: str
    verification_key: VerificationKey

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

class MessageOutputSchema(BaseModel):
    text: str
    timestamp: datetime
    message_type: MessageType
    nonce: str

    class Config:
        from_attributes = True