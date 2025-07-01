from pydantic import BaseModel

from database.models import MessageType
from schema_components.types import (
    Base64Key,
    ContactName,
    Timestamp,
)

class ContactInputSchema(BaseModel):
    name: ContactName
    verification_key: Base64Key

class MessageInputSchema(BaseModel):
    text: str
    timestamp: Timestamp
    message_type: MessageType
    nonce: str
    contact_id: int
