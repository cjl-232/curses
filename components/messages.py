import abc
import curses

from datetime import datetime

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
            output_log: Log,
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
        self._output_log = output_log
        self._scroll_index: int = 0 # Scroll upwards
        self._loaded_nonces: list[str] = list()
        self.update()

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
                self.add_item(output.text, False, title, output.timestamp)
                self._loaded_nonces.append(output.nonce)
                self.draw_required = True

    def _refresh(self):
        self._window.clear()
        self._loaded_nonces.clear()
        self._item_lines.clear()
        self._scroll_index = 0
        self._load_messages()

class MessageEntry(Entry, _MessageComponent):
    def __init__(
            self,
            engine: Engine,
            output_log: Log,
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
        self._output_log = output_log
        self._stored_inputs: dict[int, str] = dict()
        
    def handle_key(self, key: int):
        if self._contact is not None:
            if key == 10 or key == curses.KEY_ENTER:
                try:
                    raise NotImplementedError('Messaging not implemented.')
                except NotImplementedError as e:
                    self._output_log.add_item(
                        text=str(e),
                        cached=False,
                        title='NotImplementedError',
                        timestamp=datetime.now(),
                    )
                curses.curs_set(0)
                self._input = ''
                self._cursor_index = 0
                self.draw_required = True
            else:
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