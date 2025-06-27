# TODO implement absolute index and derive relative from it. Other way round is bad

import curses

from sqlalchemy import Engine

from components.base import Measurement
from components.menus import PaginatedMenu
from components.messages import MessageLog
from database.operations import get_contacts

class ContactsMenu(PaginatedMenu):
    def __init__(
            self,
            engine: Engine,
            message_log: MessageLog,
            stdscr: curses.window,
            height: Measurement,
            width: Measurement,
            top: Measurement,
            left: Measurement,
            title: str | None = None,
            focusable: bool = True,
        ):
        self.engine = engine
        self.contacts = get_contacts(engine)
        self.message_log = message_log
        super().__init__(
            items=[x.name for x in self.contacts],
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
                self.message_log.set_contact(self.contacts[self.cursor_index])
            case _:
                super().handle_key(key)

    def _refresh(self):
        self.contacts = get_contacts(self.engine)
        self.items = [x.name for x in self.contacts]