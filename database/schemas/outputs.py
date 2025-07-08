from datetime import datetime

from pydantic import AliasChoices, BaseModel, Field

from database.models import MessageType
from schema_components.types import PrivateExchangeKey, VerificationKey

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

class SentKeyOutputSchema(BaseModel):
    id: int
    contact_id: int
    private_key: PrivateExchangeKey = Field(
        validation_alias=AliasChoices('private_key', 'encoded_private_bytes'),
    )

    class Config:
        from_attributes = True