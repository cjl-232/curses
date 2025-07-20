import curses

from base64 import urlsafe_b64decode
from enum import Enum

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import (
    load_pem_public_key,
    load_der_public_key,
)
from sqlalchemy import Engine

from components.menus import PaginatedMenu
from components.prompts import Prompt, ChoicePromptNode, TextPromptNode
from database.operations import get_contacts
from states import State
from styling import Layout, Padding

class ContactsMenu(PaginatedMenu):
    def __init__(
            self,
            engine: Engine,
            layout: Layout,
            padding: Padding | None = None,
        ) -> None:
        self.engine = engine
        self.contacts = get_contacts(self.engine)
        items = [contact.name for contact in self.contacts]
        title = 'Contacts'
        footer = 'Ctrl-K: Send Key'
        super().__init__(items, layout, padding, title, footer)

    def handle_key(self, key: int) -> State:
        match key:
            case 11:  # Ctrl-K
                return State.SEND_EXCHANGE_KEY
            case curses.KEY_F5:
                self.refresh()
            case curses.KEY_ENTER | 10:
                return State.SELECT_CONTACT
            case _:
                super().handle_key(key)
        return State.STANDARD

    def refresh(self):
        if self.contacts:
            initial_contact_id = self.contacts[self.cursor_index].id
        else:
            initial_contact_id = None
        self.contacts = get_contacts(self.engine)
        self.items = [x.name for x in self.contacts]
        if initial_contact_id is not None:
            if self.contacts[self.cursor_index].id != initial_contact_id:
                for index, contact in enumerate(self.contacts):
                    if contact.id == initial_contact_id:
                        self.cursor_index = index
                        break

    @property
    def current_contact(self):
        return self.contacts[self.cursor_index]


class _KeyEntryMethod(Enum):
    HEX = 'Hexadecimal Value'
    BASE64 = 'Base64 Value'
    PEM = 'PEM-Encoded File'
    DER = 'DER-Encoded File'

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
            _KeyEntryMethod.PEM,
            _KeyEntryMethod.DER,
        )
        self.key_node = TextPromptNode(
            name='public_key',
            message='Enter the public key or its source.',
        )
        super().__init__(self.name_node, self.key_method_node, self.key_node)
    
    def retrieve_contact(self) -> tuple[str, Ed25519PublicKey]:
        name = self.name_node.input
        match self.key_method_node.input:
            case _KeyEntryMethod.HEX:
                key_bytes = bytes.fromhex(self.key_node.input)
                public_key = Ed25519PublicKey.from_public_bytes(key_bytes)
            case _KeyEntryMethod.BASE64:
                key_bytes = urlsafe_b64decode(self.key_node.input)
                public_key = Ed25519PublicKey.from_public_bytes(key_bytes)
            case _KeyEntryMethod.PEM:
                with open(self.key_node.input, 'rb') as file:
                    data = file.read()
                public_key = load_pem_public_key(data)
            case _KeyEntryMethod.DER:
                with open(self.key_node.input, 'rb') as file:
                    data = file.read()
                public_key = load_der_public_key(data)
        if not isinstance(public_key, Ed25519PublicKey):
            raise ValueError('An Ed25519 public key is required.')
        return name, public_key



