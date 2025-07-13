from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime, String, Text

def _values_callable(x: type[Enum]):
    return [i.value for i in x]

class _ContactRelationshipMixin:
    contact_id: Mapped[int] = mapped_column(ForeignKey(column='contacts.id'))

    @declared_attr
    def contact(cls) -> Mapped['Contact']:
        return relationship(Contact)


class _KeyMixin:
    encoded_bytes: Mapped[str] = mapped_column(String(44), nullable=False)


class _TimestampMixin:
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)


class Contact(Base):
    __tablename__ = 'contacts'

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    verification_key: Mapped[str] = mapped_column(
        String(44),
        unique=True,
        nullable=False,
    )
    fernet_keys: Mapped[list['FernetKey']] = relationship(
        argument='FernetKey',
        order_by='FernetKey.timestamp.desc()',
    )


class MessageType(Enum):
    SENT = 'S'
    RECEIVED = 'R'


class Message(Base, _ContactRelationshipMixin, _TimestampMixin):
    __tablename__ = 'messages'
    __table_args__ = (
        Index(
            'messages_contact_timestamp_nonce_index',
            'contact_id',
            'timestamp',
            'nonce',
        ),
    )
    text: Mapped[str] = mapped_column(Text(), nullable=False)
    nonce: Mapped[str] = mapped_column(String(32), unique=True)
    message_type: Mapped[MessageType] = mapped_column(
        SQLEnum(MessageType, values_callable=_values_callable),
    )


class FernetKey(Base, _ContactRelationshipMixin, _KeyMixin, _TimestampMixin):
    __tablename__ = 'fernet_keys'


class ReceivedExchangeKey(Base, _ContactRelationshipMixin, _KeyMixin):
    __tablename__ = 'received_exchange_keys'
    
    matched: Mapped[bool] = mapped_column(default=False, index=True)


class SentExchangeKey(Base, _ContactRelationshipMixin):
    __tablename__ = 'sent_exchange_keys'

    encoded_private_bytes: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
    )
    encoded_public_bytes: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
    )