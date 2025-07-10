import abc

from base64 import urlsafe_b64encode
from functools import cached_property

from pydantic import AliasChoices, BaseModel, Field

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
    signature: RawSignature

    @cached_property
    def sender_public_key_b64(self) -> str:
        raw_bytes = self.sender_public_key.public_bytes_raw()
        return urlsafe_b64encode(raw_bytes).decode()

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
    received_exchange_key: PublicExchangeKey = Field(
        validation_alias=AliasChoices(
            'received_exchange_key',
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

    @cached_property
    def received_exchange_key_b64(self) -> str:
        raw_bytes = self.received_exchange_key.public_bytes_raw()
        return urlsafe_b64encode(raw_bytes).decode()
    
    @cached_property
    def initial_exchange_key_b64(self) -> str | None:
        if self.initial_exchange_key is not None:
            raw_bytes = self.initial_exchange_key.public_bytes_raw()
            return urlsafe_b64encode(raw_bytes).decode()
        else:
            return None

    def _get_data(self) -> bytes:
        return self.received_exchange_key.public_bytes_raw()


class _FetchResponseMessage(_FetchResponseElement, _NonceMixin):
    encrypted_text: str

    def _get_data(self) -> bytes:
        return self.encrypted_text.encode()


class _FetchResponseData(BaseModel):
    exchange_keys: list[_FetchResponseExchangeKey]
    messages: list[_FetchResponseMessage]


class FetchResponseSchema(_BaseResponseSchema):
    data: _FetchResponseData

class _PostExchangeKeyResponseData(BaseModel):
    timestamp: Timestamp

class PostExchangeKeyResponseSchema(_BaseResponseSchema):
    data: _PostExchangeKeyResponseData