# TODO implement absolute index and derive relative from it. Other way round is bad

import curses

from sqlalchemy import Engine

from components.base import Measurement
from components.menus import PaginatedMenu
from database.operations import get_contacts

# class AddContactDialog(Component):
#     def __init__(
#             self,
#             used_names: set[str],
#             used_key_bytes: set[bytes],
#         ):
#         self.used_names = used_names
#         self.used_key_bytes = used_key_bytes

#     def run(
#             self,
#             stdscr: curses.window,
#         ) -> ContactInputSchema | None:
#         name_prompt = InputPrompt(
#             message='Enter a name for the contact.',
#             max_length=255,
#         )
#         while True:
#             name = name_prompt.run(stdscr)
#             if name is None:
#                 return None
#             elif name:
#                 name_prompt.errors.clear()
#                 if name in self.used_names:
#                     name_prompt.errors.append('Name already in use.')
#                 else:
#                     break
#         key_method_prompt = ChoicePrompt(
#             'Select a method to enter the contact\'s public key.',
#             [
#                 'Base64',
#                 'Hexadecimal',
#                 'PEM-Encoded File',
#             ],
#         )
#         match key_method_prompt.run(stdscr):
#             case 1:
#                 key_prompt = Base64Prompt(
#                     message=(
#                         'Enter the contact\'s public key in Base64-encoded '
#                         'form.'
#                     ),
#                     max_length=44,
#                     n_bytes=32,
#                 )
#             case 2:
#                 key_prompt = HexadecimalPrompt(
#                     message=(
#                         'Enter the contact\'s public key in non-negative '
#                         'hexadecimal form.'
#                     ),
#                     max_length=64,
#                     n_bytes=32,
#                 )
#             case 3:
#                 key_prompt = Base64Prompt(
#                     message=(
#                         'Enter the contact\'s public key in Base64-encoded '
#                         'form.'
#                     ),
#                     max_length=44,
#                     n_bytes=32,
#                 )
#             case _:
#                 return None
#         while True:
#             input = key_prompt.run(stdscr)
#             if input is None:
#                 return None
#             elif input in self.used_key_bytes:
#                 key_prompt.errors = ['Key already in use.']
#             else:
#                 break
#         verification_key = Ed25519PublicKey.from_public_bytes(input)
#         result = ContactInputSchema.model_validate({
#             'name': name,
#             'verification_key': verification_key,
#         })
#         return result


# Need to include an argument for the message log window

class ContactsMenu(PaginatedMenu):
    def __init__(
            self,
            engine: Engine,
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
                print('refresh')
            case curses.KEY_ENTER | 10:
                print(self.contacts[self.cursor_index].name)
            case _:
                super().handle_key(key)
        

    def _refresh(self):
        self.contacts = get_contacts(self.engine)
        self.items = [x.name for x in self.contacts]