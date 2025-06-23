import binascii
import curses

from base64 import urlsafe_b64decode

from sqlalchemy import Engine

from components.base import Component
from components.prompts import Prompt
from database.operations import get_contacts

class AddContactDialog(Component):
    def __init__(
            self,
            used_names: set[str],
            used_key_bytes: set[bytes],
        ):
        self.used_names = used_names
        self.used_key_bytes = used_key_bytes

    def run(self, stdscr: curses.window):
        name_prompt = Prompt('Enter a name for the contact.')
        while True:
            name_prompt.run(stdscr)
            if name_prompt.cancelled:
                return
            elif name_prompt.entry:
                name_prompt.errors.clear()
                if name_prompt.entry in self.used_names:
                    name_prompt.errors.append('Name already in use.')
                else:
                    break
        key_prompt = Prompt('Enter a public key for the contact.')
        while True:
            key_prompt.run(stdscr)
            if key_prompt.cancelled:
                return
            elif key_prompt.entry:
                key_prompt.errors.clear()
                try:
                    key_bytes = urlsafe_b64decode(key_prompt.entry)
                    if key_bytes in self.used_key_bytes:
                        key_prompt.errors.append('Key already in use.')
                    elif len(key_bytes) != 32:
                        key_prompt.errors.append(
                            'Key must have an unencoded length of 32 bytes.',
                        )
                    else:
                        break
                except binascii.Error:
                    key_prompt.errors.append('Key is not valid Base64.')
                
                

        print(name_prompt.entry, key_bytes)
        exit()
        stdscr.clear()
        curses.curs_set(1)
        stdscr.nodelay(False)
        height, width = stdscr.getmaxyx()
        stdscr.addstr(0, 0, 'Dialog')
        stdscr.getch()

        

class ContactsMenu(Component):
    def __init__(self, engine: Engine):
        self.engine = engine
        self.contacts = get_contacts(engine)
        self.cursor_index = 0
        self.page_index = 0

    def run(self, stdscr: curses.window):
        while True:
            # Clear the screen and set properties each loop.
            stdscr.clear()
            curses.curs_set(0)
            stdscr.nodelay(True)

            # Extract height information.
            height = stdscr.getmaxyx()[0]
            if height > 1:
                page_count = 1 + len(self.contacts) // (height - 1)
            else:
                page_count = len(self.contacts)
            if self.page_index < 0:
                self.page_index = 0
            elif self.page_index >= page_count:
                self.page_index = page_count - 1

            # Extract the relevant contacts:
            start_index = self.page_index * (height - 1)
            stop_index = start_index + (height - 1)
            page_contacts = self.contacts[start_index:stop_index]
            if self.cursor_index < 0:
                self.cursor_index = 0
            elif self.cursor_index >= len(page_contacts):
                self.cursor_index = len(page_contacts) - 1

            # Populate the screen with existing contacts.
            for index, contact in enumerate(page_contacts):
                if index != self.cursor_index:
                    stdscr.addstr(index, 0, contact.name)
                else:
                    stdscr.addstr(index, 0, contact.name, curses.A_REVERSE)
                    
            # Add a display indicating the current page.
            page_text = f'Page {self.page_index + 1} of {page_count}'
            stdscr.addstr(height - 1, 0, page_text)
            
            # for i, contact in enumerate(self.contacts):
            #     if i == self.cursor_index:
            #         stdscr.attron(curses.A_REVERSE)
            #         stdscr.addstr(i, 0, contact.name)
            #         stdscr.attroff(curses.A_REVERSE)
            #     else:
            #         stdscr.addstr(i, 0, contact.name)
            
            # # Append an option to add a contact.
            # if self.cursor_index == len(self.contacts):
            #     stdscr.attron(curses.A_REVERSE)
            #     stdscr.addstr(len(self.contacts), 0, 'Add Contact')
            #     stdscr.attroff(curses.A_REVERSE)
            # else:
            #     stdscr.addstr(len(self.contacts), 0, 'Add Contact')

            # Refresh the screen.
            stdscr.refresh()
            
            # Read and handle user input.
            match stdscr.getch():
                case curses.KEY_UP:
                    self.cursor_index -= 1
                case curses.KEY_DOWN:
                    self.cursor_index += 1
                case curses.KEY_LEFT:
                    self.page_index -= 1
                case curses.KEY_RIGHT:
                    self.page_index += 1
                case curses.KEY_HOME | curses.KEY_PPAGE:
                    self.cursor_index = 0
                case curses.KEY_END | curses.KEY_NPAGE:
                    self.cursor_index = len(self.contacts)
                case 10:
                    if self.cursor_index < len(self.contacts):
                        pass
                    else:
                        used_names: set[str] = set([
                            contact.name
                            for contact in self.contacts
                        ])
                        used_key_bytes: set[bytes] = set([
                            contact.verification_key.public_bytes_raw()
                            for contact in self.contacts
                        ])
                        dialog = AddContactDialog(used_names, used_key_bytes)
                        dialog.run(stdscr)
                case 27:
                    while True:
                        x = stdscr.getch()
                        if x != -1:
                            print(x)
                            break

                    return
                case 81 | 113:
                    exit()
                case _:
                    pass

if __name__ == '__main__':
    from secrets import token_hex, token_urlsafe
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from settings import settings
    from database.models import Base, Contact
    engine = create_engine(settings.local_database.url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        for _ in range(20):
            session.add(Contact(name=token_hex(16), verification_key=token_urlsafe(32)+'='))
        session.commit()
    menu = ContactsMenu(engine)
    curses.wrapper(menu.run)

