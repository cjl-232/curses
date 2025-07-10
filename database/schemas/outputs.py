from datetime import datetime

from pydantic import AliasChoices, BaseModel, Field

from database.models import MessageType
from schema_components.types import (
    PrivateExchangeKey,
    PublicExchangeKey,
    VerificationKey,
)

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

class ReceivedKeyOutputSchema(BaseModel):
    id: int
    contact: ContactOutputSchema
    public_key: PublicExchangeKey = Field(
        validation_alias=AliasChoices('public_key', 'encoded_bytes'),
    )

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

class SentKeyOutputSchema(BaseModel):
    id: int
    contact: ContactOutputSchema
    private_key: PrivateExchangeKey = Field(
        validation_alias=AliasChoices('private_key', 'encoded_private_bytes'),
    )

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True