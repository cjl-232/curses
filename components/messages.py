import abc
import curses

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from components.base import Measurement
from components.entries import Entry
from components.logs import Log
from database.models import Message, MessageType
from database.outputs.schemas import ContactOutputSchema, MessageOutputSchema

class _MessageComponent(metaclass=abc.ABCMeta):
    _engine: Engine
    _contact: ContactOutputSchema | None

    def set_contact(self, contact: ContactOutputSchema | None) -> bool:
        if self._contact != contact:
            self._contact = contact
            return True
        return False

class MessageLog(Log, _MessageComponent):
    def __init__(
            self,
            engine: Engine,
            contact: ContactOutputSchema | None,
            stdscr: curses.window,
            height: Measurement,
            width: Measurement,
            top: Measurement,
            left: Measurement,
        ):
        super().__init__(
            stdscr=stdscr,
            height=height,
            width=width,
            top=top,
            left=left,
            title=contact.name if contact is not None else None,
        )
        self._engine = engine
        self._contact = contact
        self._scroll_index: int = 0 # Scroll upwards
        self._message_lines: list[tuple[str, bool]] = list()
        self._loaded_nonces: list[str] = list()

    def handle_key(self, key: int):
        if key == curses.KEY_F5:
            self.update()
        elif key == 281: # SHIFT-F5
            self._refresh()
        else:
            super().handle_key(key)

    def set_contact(self, contact: ContactOutputSchema | None) -> bool:
        contact_replaced = super().set_contact(contact)
        if contact_replaced:
            if self._contact is not None:
                self._title = self._contact.name
            else:
                self._title = None
            self._refresh()
            self.draw_required = True
        return contact_replaced

    def update(self):
        self._load_messages()

    def _load_messages(self):
        if self._contact is None:
            return
        with Session(self._engine) as session:
            query = (
                select(Message)
                .where(Message.contact_id == self._contact.id)
                .where(~Message.nonce.in_(self._loaded_nonces))
                .order_by(Message.timestamp)
            )
            for obj in session.scalars(query):
                output = MessageOutputSchema.model_validate(obj)
                if output.message_type == MessageType.RECEIVED:
                    title = f'{self._contact.name}:'
                else:
                    title = 'You:'
                self.add_item(output.text, title, output.timestamp)
                self._loaded_nonces.append(output.nonce)
                self.draw_required = True

    def _refresh(self):
        self._loaded_nonces.clear()
        self._message_lines.clear()
        self._scroll_index = 0
        self._load_messages()

class MessageEntry(Entry, _MessageComponent):
    def __init__(
            self,
            engine: Engine,
            contact: ContactOutputSchema | None,
            stdscr: curses.window,
            height: Measurement,
            width: Measurement,
            top: Measurement,
            left: Measurement,
        ):
        super().__init__(
            stdscr=stdscr,
            height=height,
            width=width,
            top=top,
            left=left,
            title='Message Entry',
        )
        self._engine = engine
        self._contact = contact
        self._stored_inputs: dict[int, str] = dict()
        
    def handle_key(self, key: int):
        if self._contact is not None:
            super().handle_key(key)

    def set_contact(self, contact: ContactOutputSchema | None) -> bool:
        if self._contact is not None:
            self._stored_inputs[self._contact.id] = self._input
        contact_replaced = super().set_contact(contact)
        if contact_replaced:
            if self._contact is not None:
                self._input = self._stored_inputs.get(self._contact.id, '')
            self._cursor_index = 0
            self.draw_required = True
        return contact_replaced