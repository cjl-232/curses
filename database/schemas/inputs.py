from pydantic import BaseModel

from database.models import MessageType
from schema_components.types import Base64Key, Timestamp

class ContactInputSchema(BaseModel):
    name: str
    verification_key: Base64Key

class MessageInputSchema(BaseModel):
    text: str
    timestamp: Timestamp
    message_type: MessageType
    nonce: str
    contact_id: int

class ReceivedKeyInputSchema(BaseModel):
    encoded_bytes: Base64Key
    contact_id: int

class SentKeyInputSchema(BaseModel):
    encoded_private_bytes: Base64Key
    encoded_public_bytes: Base64Key
    contact_id: int
