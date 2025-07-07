# TODO implement absolute index and derive relative from it. Other way round is bad

import curses

from enum import Enum

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import Engine

from components.base import Measurement
from components.menus import PaginatedMenu
from components.messages import MessageEntry, MessageLog
from components.prompts import Prompt, ChoicePromptNode, TextPromptNode
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

class _KeyEntryMethod(Enum):
    HEX = 'Hexadecimal Value'
    BASE64 = 'Base64 Value'
    PEMFILE = 'PEM-Encoded File'
    DERFILE = 'DER-Encoded File'

class ContactsPrompt(Prompt):
    def __init__(self) -> None:
        self.name_node = TextPromptNode(
            name='name',
            message='Enter a unique name for this contact.',
        )
        self.key_method_node = ChoicePromptNode[_KeyEntryMethod](
            'key_method',
            "Select an entry method for this contact's public key.",
            _KeyEntryMethod.HEX,
            _KeyEntryMethod.BASE64,
            _KeyEntryMethod.PEMFILE,
            _KeyEntryMethod.DERFILE,
        )
        self.key_node = TextPromptNode(
            name='public_key',
            message='Enter a unique public key for this contact.',
        )
        super().__init__(self.name_node, self.key_method_node, self.key_node)
    
    def retrieve_contact(self) -> tuple[str, Ed25519PublicKey]:
        name = self.name_node.input
        match self.key_method_node.input:
            case _KeyEntryMethod.HEX:
                key_bytes = bytes.fromhex(self.key_node.input)
            case _:
                return None
        return name, Ed25519PublicKey.from_public_bytes(key_bytes)



