import abc

from base64 import urlsafe_b64encode
from typing import Self

from pydantic import AliasChoices, BaseModel, Field, model_validator

from schema_components.types import (
    PublicExchangeKey,
    RawSignature,
    Timestamp,
    VerificationKey,
)

class _BaseResponseSchema(BaseModel):
    status: str
    message: str

class _NonceMixin:
    nonce: str = Field(pattern='^(?:[0-9a-fA-F]{2})+$')


class _TimestampMixin:
    timestamp: Timestamp


class _PostMessageResponseData(BaseModel, _NonceMixin, _TimestampMixin):
    pass


class _PostKeyResponseData(BaseModel, _TimestampMixin):
    pass


class PostMessageResponseSchema(_BaseResponseSchema):
    data: _PostMessageResponseData


class PostKeyResponseSchema(_BaseResponseSchema):
    data: _PostKeyResponseData


class _FetchResponseElement(BaseModel, _TimestampMixin, metaclass=abc.ABCMeta):
    sender_public_key: VerificationKey = Field(
        validation_alias=AliasChoices(
            'sender_public_key',
            'sender_verification_key',
            'sender_key',
        ),
    )
    sender_public_key_b64: str
    signature: RawSignature

    @model_validator(mode='after')
    def preserve_base64_sender_key(self) -> Self:
        raw_key_bytes = self.sender_public_key.public_bytes_raw()
        b64_key_bytes = urlsafe_b64encode(raw_key_bytes)
        self.sender_public_key_b64 = b64_key_bytes.decode()
        return self

    @abc.abstractmethod
    def _get_data(self) -> bytes:
        pass

    @property
    def is_valid(self) -> bool:
        try:
            self.sender_public_key.verify(self.signature, self._get_data())
            return True
        except Exception:
            return False

    class Config:
        arbitrary_types_allowed=True


class _FetchResponseExchangeKey(_FetchResponseElement):
    sent_exchange_key: PublicExchangeKey = Field(
        validation_alias=AliasChoices(
            'sent_exchange_key',
            'key',
            'exchange_key',
            'sent_exchange_key',
            'transmitted_key',
            'transmitted_exchange_key',
        ),
    )
    initial_exchange_key: PublicExchangeKey | None = Field(
        default=None,
        validation_alias=AliasChoices(
            'initial_exchange_key',
            'response_to',
        ),
    )

    def _get_data(self) -> bytes:
        return self.sent_exchange_key.public_bytes_raw()


class _FetchResponseMessage(_FetchResponseElement, _NonceMixin):
    encrypted_text: str

    def _get_data(self) -> bytes:
        return self.encrypted_text.encode()


class _FetchResponseData(BaseModel):
    exchange_keys: list[_FetchResponseExchangeKey]
    messages: list[_FetchResponseMessage]


class FetchResponseSchema(_BaseResponseSchema):
    data: _FetchResponseData