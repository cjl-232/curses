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
    

# class MessageType(Enum):
#     SENT = 'S'
#     RECEIVED = 'R'

# #class Message(ConcreteBase, Base):

# class Message(Base):
#     __tablename__ = 'messages'
#     __table_args__ = (
#         Index('messages_contact_timestamp_index', 'contact_id', 'timestamp'),
#     )

#     id: Mapped[int] = mapped_column(
#         primary_key=True,
#     )
#     text: Mapped[str] = mapped_column(
#         Text(),
#         nullable=False,
#     )
#     timestamp: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         nullable=False,
#     )
#     message_type: Mapped[MessageType] = mapped_column(
#         SQLEnum(MessageType, values_callable=_values_callable),
#     )
#     nonce: Mapped[str] = mapped_column(
#         String(32),
#         unique=True,
#     )
#     contact_id: Mapped[int] = mapped_column(
#         ForeignKey(column=Contact.id),
#     )
#     contact: Mapped[Contact] = relationship(back_populates='messages')

    
# class TransmittedMessage(
#     AbstractConcreteBase,
#     Base,
#     _MessageMixin,
#     _TimestampMixin,
# ):
#     nonce: Mapped[str] = mapped_column(String(32), unique=True)

# class ReceivedMessage(TransmittedMessage):
#     __tablename__ = 'received_messages'
#     __mapper_args__ = {
#         'concrete': True,
#         'polymorphic_identity': 'received',
#     }

# class SentMessage(TransmittedMessage):
#     __tablename__ = 'sent_messages'
#     __mapper_args__ = {
#         'concrete': True,
#         'polymorphic_identity': 'sent',
#     }



# class Base

# from datetime import datetime
# from enum import Enum

# from sqlalchemy import Enum as SQLEnum, ForeignKey, Index
# from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
# from sqlalchemy.types import DateTime, String, Text

# def _values_callable(x: type[Enum]):
#     return [i.value for i in x]

# class Base(DeclarativeBase):
#     pass

# class Contact(Base):
#     __tablename__ = 'contacts'

#     id: Mapped[int] = mapped_column(
#         primary_key=True
#     )
#     name: Mapped[str] = mapped_column(
#         String(255),
#         unique=True,
#         nullable=False,
#     )
#     public_key: Mapped[str] = mapped_column(
#         String(44),
#         unique=True,
#         nullable=False,
#     )
#     messages: Mapped[list['Message']] = relationship(
#         back_populates='contact',
#         cascade='all, delete-orphan',
#     )
#     fernet_keys: Mapped[list['FernetKey']] = relationship(
#         back_populates='contact',
#         cascade='all, delete-orphan',
#         order_by='FernetKey.timestamp',
#     )
#     received_keys: Mapped[list['ReceivedKey']] = relationship(
#         back_populates='contact',
#         cascade='all, delete-orphan',
#     )
#     sent_keys: Mapped[list['SentKey']] = relationship(
#         back_populates='contact',
#         cascade='all, delete-orphan',
#     )

# class MessageType(Enum):
#     SENT = 'S'
#     RECEIVED = 'R'

# class Message(Base):
#     __tablename__ = 'messages'
#     __table_args__ = (
#         Index('messages_contact_timestamp_index', 'contact_id', 'timestamp'),
#     )

#     id: Mapped[int] = mapped_column(
#         primary_key=True,
#     )
#     text: Mapped[str] = mapped_column(
#         Text(),
#         nullable=False,
#     )
#     timestamp: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         nullable=False,
#     )
#     message_type: Mapped[MessageType] = mapped_column(
#         SQLEnum(MessageType, values_callable=_values_callable),
#     )
#     nonce: Mapped[str] = mapped_column(
#         String(32),
#         unique=True,
#     )
#     contact_id: Mapped[int] = mapped_column(
#         ForeignKey(
#             column=Contact.id,
#         ),
#     )
#     contact: Mapped[Contact] = relationship()

# class KeyType(Enum):
#     EPHEMERAL = 'E'
#     COMPLETE = 'C'

# class FernetKey(Base):
#     __tablename__ = 'fernet_keys'
#     id: Mapped[int] = mapped_column(
#         primary_key=True,
#     )
#     key: Mapped[str] = mapped_column(
#         String(44),
#         nullable=False,
#         unique=True,
#     )
#     timestamp: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         nullable=False,
#     )
#     contact_id: Mapped[int] = mapped_column(
#         ForeignKey(
#             column=Contact.id,
#         ),
#     )
#     contact: Mapped[Contact] = relationship()
#     received_key: Mapped['ReceivedKey'] = relationship(
#         back_populates='fernet_key',
#     )

# class SentKey(Base):
#     __tablename__ = 'sent_keys'
#     id: Mapped[int] = mapped_column(
#         primary_key=True,
#     )
#     private_key: Mapped[str] = mapped_column(
#         String(44),
#         nullable=False,
#         unique=True,
#     )
#     public_key: Mapped[str] = mapped_column(
#         String(44),
#         nullable=False,
#         unique=True,
#     )
#     received_keys: Mapped[list['ReceivedKey']] = relationship(
#         back_populates='sent_key',
#     )
#     contact_id: Mapped[int] = mapped_column(
#         ForeignKey(
#             column=Contact.id,
#         ),
#     )
#     contact: Mapped[Contact] = relationship(
#         back_populates='sent_keys',
#     )

# class ReceivedKey(Base):
#     __tablename__ = 'received_keys'
#     id: Mapped[int] = mapped_column(
#         primary_key=True,
#     )
#     public_key: Mapped[str] = mapped_column(
#         String(44),
#         nullable=False,
#         unique=True,
#     )
#     timestamp: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         nullable=False,
#     )
#     contact_id: Mapped[int] = mapped_column(
#         ForeignKey(
#             column=Contact.id,
#         ),
#     )
#     contact: Mapped[Contact] = relationship(
#         back_populates='received_keys',
#     )
#     sent_key_id: Mapped[int | None] = mapped_column(
#         ForeignKey(
#             column=SentKey.id,
#         ),
#         nullable=True,
#         default=None,
#     )
#     sent_key: Mapped[SentKey | None] = relationship(
#         back_populates='received_keys',
#     )
#     fernet_key_id: Mapped[int | None] = mapped_column(
#         ForeignKey(
#             column=FernetKey.id,
#         ),
#         unique=True,
#         nullable=True,
#         default=None,
#     )
#     fernet_key: Mapped[FernetKey | None] = relationship(
#         back_populates='received_key',
#         single_parent=True,
#     )