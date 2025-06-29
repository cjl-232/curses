# TODO implement absolute index and derive relative from it. Other way round is bad

import curses

from sqlalchemy import Engine

from components.base import Measurement
from components.menus import PaginatedMenu
from components.messages import MessageEntry, MessageLog
from database.operations import get_contacts

class ContactsMenu(PaginatedMenu):
    def __init__(
            self,
            engine: Engine,
            message_entry: MessageEntry,
            message_log: MessageLog,
            stdscr: curses.window,
            height: Measurement,
            width: Measurement,
            top: Measurement,
            left: Measurement,
            title: str | None = None,
            focusable: bool = True,
        ):
        self._engine = engine
        self._contacts = get_contacts(engine)
        self._message_entry = message_entry
        self._message_log = message_log
        super().__init__(
            items=[x.name for x in self._contacts],
            stdscr=stdscr,
            height=height,
            width=width,
            top=top,
            left=left,
            title=title,
            focusable=focusable,
        )

    def handle_key(self, key: int):
        match key:
            case curses.KEY_F5:
                self._refresh()
            case curses.KEY_ENTER | 10:
                contact = self._contacts[self._cursor_index]
                self._message_log.set_contact(contact)
                self._message_entry.set_contact(contact)
            case _:
                super().handle_key(key)

    def _refresh(self):
        self._contacts = get_contacts(self._engine)
        self._items = [x.name for x in self._contacts]