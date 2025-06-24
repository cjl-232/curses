# TODO implement absolute index and derive relative from it. Other way round is bad

import curses

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from components.base import Component
from components.menus import PaginatedMenu
from components.messages import MessagesScreen
from components.prompts import (
    Base64Prompt,
    ChoicePrompt,
    HexadecimalPrompt,
    InputPrompt,
)
from database.inputs.schemas import ContactInputSchema
from database.models import Contact
from database.operations import get_contacts
from database.outputs.schemas import ContactOutputSchema

class AddContactDialog(Component):
    def __init__(
            self,
            used_names: set[str],
            used_key_bytes: set[bytes],
        ):
        self.used_names = used_names
        self.used_key_bytes = used_key_bytes

    def run(
            self,
            stdscr: curses.window,
        ) -> ContactInputSchema | None:
        name_prompt = InputPrompt(
            message='Enter a name for the contact.',
            max_length=255,
        )
        while True:
            name = name_prompt.run(stdscr)
            if name is None:
                return None
            elif name:
                name_prompt.errors.clear()
                if name in self.used_names:
                    name_prompt.errors.append('Name already in use.')
                else:
                    break
        key_method_prompt = ChoicePrompt(
            'Select a method to enter the contact\'s public key.',
            [
                'Base64',
                'Hexadecimal',
                'PEM-Encoded File',
            ],
        )
        match key_method_prompt.run(stdscr):
            case 1:
                key_prompt = Base64Prompt(
                    message=(
                        'Enter the contact\'s public key in Base64-encoded '
                        'form.'
                    ),
                    max_length=44,
                    n_bytes=32,
                )
            case 2:
                key_prompt = HexadecimalPrompt(
                    message=(
                        'Enter the contact\'s public key in non-negative '
                        'hexadecimal form.'
                    ),
                    max_length=64,
                    n_bytes=32,
                )
            case 3:
                key_prompt = Base64Prompt(
                    message=(
                        'Enter the contact\'s public key in Base64-encoded '
                        'form.'
                    ),
                    max_length=44,
                    n_bytes=32,
                )
            case _:
                return None
        while True:
            input = key_prompt.run(stdscr)
            if input is None:
                return None
            elif input in self.used_key_bytes:
                key_prompt.errors = ['Key already in use.']
            else:
                break
        verification_key = Ed25519PublicKey.from_public_bytes(input)
        result = ContactInputSchema.model_validate({
            'name': name,
            'verification_key': verification_key,
        })
        return result

        

class ContactsMenu(PaginatedMenu):
    def __init__(self, engine: Engine, contacts: list[ContactOutputSchema]):
        super().__init__(
            title='Contacts',
            items=[x.name for x in contacts],
            break_after_action=False,
            additional_key_mappings={
                curses.KEY_F5: self._refresh,
                curses.KEY_F10: self._add_contact,
            },
        )
        self.engine = engine
        self.contacts = get_contacts(engine)

    def _refresh(self, _: curses.window):
        self.contacts = get_contacts(self.engine)
        self.items = [x.name for x in self.contacts]

    def _add_contact(self, stdscr: curses.window):
        used_names = set([x.name for x in self.contacts])
        used_key_bytes = set([
            contact.verification_key.public_bytes_raw()
            for contact in self.contacts
        ])
        input_prompt = AddContactDialog(used_names, used_key_bytes)
        input = input_prompt.run(stdscr)
        if input is not None:
            if input.name < self.contacts[self.cursor_index].name:
                self.cursor_index += 1
            with Session(self.engine) as session:
                session.add(Contact(**input.model_dump()))
                session.commit()
            self._refresh(stdscr)

    def handle_selection(self, stdscr: curses.window, cursor_index: int):
        messages_screen = MessagesScreen(self.contacts[cursor_index])
        messages_screen.run(stdscr)



# class ContactsMenu(Component):
#     def __init__(self, engine: Engine):
#         self.engine = engine
#         self.contacts = get_contacts(engine)
#         self.cursor_index = 0
#         self.page_index = 0

#     def run(self, stdscr: curses.window):
#         while True:
#             # Clear the screen and set properties each loop.
#             stdscr.clear()
#             curses.curs_set(0)
#             stdscr.nodelay(True)

#             # Extract height information, and enforce a minimum.
#             height = stdscr.getmaxyx()[0]
#             if height < 2:
#                 stdscr.addstr(height - 1, 0, 'Insufficient terminal height.')
#                 stdscr.refresh()
#                 continue
#             contacts_per_page = height - 1
#             if contacts_per_page > settings.display.max_page_height:
#                 contacts_per_page = settings.display.max_page_height

#             if height > 1:
#                 page_count = math.ceil(len(self.contacts) / contacts_per_page)
#             else:
#                 page_count = len(self.contacts)
#             if self.page_index < 0:
#                 self.page_index = page_count - 1
#             elif self.page_index >= page_count:
#                 self.page_index = 0

#             # Extract the relevant contacts:
#             start_index = self.page_index * contacts_per_page
#             stop_index = start_index + contacts_per_page
#             page_contacts = self.contacts[start_index:stop_index]
#             if self.cursor_index < 0:
#                 if self.page_index > 0:
#                     self.page_index -= 1
#                     self.cursor_index = contacts_per_page - 1
#                 else:
#                     self.cursor_index = 0
#             elif self.cursor_index >= len(page_contacts):
#                 if self.page_index < page_count - 1:
#                     self.page_index += 1
#                     self.cursor_index = 0
#                 else:
#                     self.cursor_index = len(page_contacts) - 1

#             # Populate the screen with existing contacts.
#             contacts_line = height - 1 - contacts_per_page
#             for index, contact in enumerate(page_contacts):
#                 if index != self.cursor_index:
#                     stdscr.addstr(contacts_line + index, 0, contact.name)
#                 else:
#                     stdscr.attron(curses.A_REVERSE)
#                     stdscr.addstr(contacts_line + index, 0, contact.name)
#                     stdscr.attroff(curses.A_REVERSE)
                    
#             # Add a display indicating the current page.
#             page_text = f'Page {self.page_index + 1} of {page_count}'
#             stdscr.addstr(height - 1, 0, page_text)
            
#             # for i, contact in enumerate(self.contacts):
#             #     if i == self.cursor_index:
#             #         stdscr.attron(curses.A_REVERSE)
#             #         stdscr.addstr(i, 0, contact.name)
#             #         stdscr.attroff(curses.A_REVERSE)
#             #     else:
#             #         stdscr.addstr(i, 0, contact.name)
            
#             # # Append an option to add a contact.
#             # if self.cursor_index == len(self.contacts):
#             #     stdscr.attron(curses.A_REVERSE)
#             #     stdscr.addstr(len(self.contacts), 0, 'Add Contact')
#             #     stdscr.attroff(curses.A_REVERSE)
#             # else:
#             #     stdscr.addstr(len(self.contacts), 0, 'Add Contact')

#             # Refresh the screen.
#             stdscr.refresh()
            
#             # Read and handle user input.
#             match stdscr.getch():
#                 case curses.KEY_UP:
#                     self.cursor_index -= 1
#                 case curses.KEY_DOWN:
#                     self.cursor_index += 1
#                 case curses.KEY_LEFT:
#                     self.page_index -= 1
#                 case curses.KEY_RIGHT:
#                     self.page_index += 1
#                 case curses.KEY_HOME | curses.KEY_PPAGE:
#                     self.cursor_index = 0
#                 case curses.KEY_END | curses.KEY_NPAGE:
#                     self.cursor_index = len(self.contacts)
#                 case curses.KEY_F10:
#                     used_names = set([x.name for x in self.contacts])
#                     used_key_bytes = set([
#                         contact.verification_key.public_bytes_raw()
#                         for contact in self.contacts
#                     ])
#                     input_prompt = AddContactDialog(used_names, used_key_bytes)
#                     input = input_prompt.run(stdscr)
#                     if input is not None:
#                         absolute_index = start_index + self.cursor_index
#                         if input.name < self.contacts[absolute_index].name:
#                             self.cursor_index += 1
#                             if self.cursor_index >= contacts_per_page:
#                                 self.cursor_index = 0
#                                 self.page_index += 1
#                         with Session(self.engine) as session:
#                             session.add(Contact(**input.model_dump()))
#                             session.commit()
#                         self.contacts = get_contacts(self.engine)
#                 case 27:
#                     while True:
#                         x = stdscr.getch()
#                         if x != -1:
#                             print(x)
#                             break
#                     return
#                 case 81 | 113:
#                     exit()
#                 case 10:
#                     messages = MessagesScreen(self.contacts[start_index + self.cursor_index])
#                     messages.run(stdscr)
#                 case _:
#                     pass

