import abc
import curses

from datetime import datetime

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from components.base import Measurement
from components.entries import Entry
from components.logs import Log
from database.models import Message, MessageType
from database.schemas.outputs import ContactOutputSchema, MessageOutputSchema
from states import State
from styling import Layout, Padding


class _SetContactMixin:
    def set_contact(self, contact: ContactOutputSchema | None) -> bool:
        if self.contact != contact:
            self.contact = contact
            return True
        return False

class MessageLog(Log, _SetContactMixin):
    def __init__(
            self,
            engine: Engine,
            contact: ContactOutputSchema | None,
            layout: Layout,
            padding: Padding | None = None,
            title: str | None = None,
            footer: str | None = None,
            bordered: bool = True,
            focusable: bool = True,
        ) -> None:
        super().__init__(layout, padding, title, footer, bordered, focusable)
        if not self.title and contact is not None:
            self.title = contact.name
        self.engine = engine
        self.contact = contact
        self.loaded_nonces: list[str] = list()
        self.update()

    def handle_key(self, key: int) -> State:
        match key:
            case curses.KEY_F5:
                self.update()
                return State.STANDARD
            case 281:  # Shift-F5
                self.refresh()
                return State.STANDARD
            case _:
                return super().handle_key(key)

    def set_contact(self, contact: ContactOutputSchema | None) -> bool:
        contact_replaced = super().set_contact(contact)
        if contact_replaced:
            if self.contact is not None:
                self.title = self.contact.name
            else:
                self.title = ''
            self.refresh()
            self.draw_required = True
        return contact_replaced

    def update(self):
        if self.contact is None:
            return
        with Session(self.engine) as session:
            query = (
                select(Message)
                .where(Message.contact_id == self.contact.id)
                .where(~Message.nonce.in_(self.loaded_nonces))
                .order_by(Message.timestamp)
            )
            for obj in session.scalars(query):
                output = MessageOutputSchema.model_validate(obj)
                if output.message_type == MessageType.RECEIVED:
                    title = f'{self.contact.name}:'
                else:
                    title = 'You:'
                self.add_item(output.text, False, title, output.timestamp)
                self.loaded_nonces.append(output.nonce)
                self.draw_required = True

    def refresh(self):
        self.window.erase()
        self.loaded_nonces.clear()
        self.item_lines.clear()
        self.scroll_index = 0
        self.update()

class MessageEntry(Entry, _SetContactMixin):
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