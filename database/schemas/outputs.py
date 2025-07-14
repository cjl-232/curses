from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from database.models import MessageType
from schema_components.types import (
    FernetKey,
    PrivateExchangeKey,
    PublicExchangeKey,
    VerificationKey,
)

class FernetKeyOutputSchema(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    key: FernetKey = Field(
        validation_alias=AliasChoices('key', 'encoded_bytes'),
    )


class BaseContactOutputSchema(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
    )

    id: int
    name: str
    verification_key: VerificationKey


class ContactOutputSchema(BaseContactOutputSchema):
    fernet_keys: list[FernetKeyOutputSchema]


class MessageOutputSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    text: str
    timestamp: datetime
    message_type: MessageType
    nonce: str
    

class ReceivedKeyOutputSchema(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
    )

    id: int
    contact: BaseContactOutputSchema
    public_key: PublicExchangeKey = Field(
        validation_alias=AliasChoices('public_key', 'encoded_bytes'),
    )
    

class SentKeyOutputSchema(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
    )

    id: int
    contact: BaseContactOutputSchema
    private_key: PrivateExchangeKey = Field(
        validation_alias=AliasChoices('private_key', 'encoded_private_bytes'),
    )
    public_key: PublicExchangeKey = Field(
        validation_alias=AliasChoices('public_key', 'encoded_public_bytes'),
    )