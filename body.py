# Need to work out combinations (100% - 200px)

import curses

from components.base import ComponentWindow, MeasurementUnit
from components.contacts import ContactsMenu
from components.menus import PaginatedMenu

class Example(ComponentWindow):

    def draw(self, focused: bool):
        self._window.erase()
        self._draw_border(focused)
        self._window.refresh()


    def handle_key(self, key: int):
        """Handle key presses when this window is active."""

class Menu(PaginatedMenu):
    def __init__(self, items: list[str], stdscr: curses.window, height: tuple[int | float, MeasurementUnit], width: tuple[int | float, MeasurementUnit], top: tuple[int | float, MeasurementUnit], left: tuple[int | float, MeasurementUnit], title: str | None = None, focusable: bool = True):
        super().__init__(items, stdscr, height, width, top, left, title, focusable)
    
    def handle_key(self, key: int):
        match key:
            case curses.KEY_UP:
                self.cursor_index -= 1
                if self.cursor_index < 0:
                    self.cursor_index = len(self.items) - 1
                self.draw(focused=True)
            case curses.KEY_DOWN:
                self.cursor_index += 1
                if self.cursor_index >= len(self.items):
                    self.cursor_index = 0
                self.draw(focused=True)
            case _:
                pass


from base64 import urlsafe_b64encode
from secrets import token_bytes, token_hex
from sqlalchemy import create_engine
from database.models import Base, Contact
engine = create_engine('sqlite:///contacttest.db')
Base.metadata.create_all(engine)
from sqlalchemy.orm import Session
with Session(engine) as session:
    for _ in range(20):
        contact = Contact(name=f'Contact #{token_hex(8)}', verification_key=urlsafe_b64encode(token_bytes(32)).decode())
        session.add(contact)
    session.commit()


class Body:
    def __init__(self, stdscr: curses.window):
        self.component_index = 0
        self.components: list[ComponentWindow] = [
            ContactsMenu(
                engine=engine,
                stdscr=stdscr,
                height=(0.8, MeasurementUnit.PERCENTAGE),
                width=(0.2, MeasurementUnit.PERCENTAGE),
                top=(0, MeasurementUnit.PIXELS),
                left=(0, MeasurementUnit.PIXELS),
                title='Contacts',
            ),
            Example(
                stdscr=stdscr,
                height=(0.8, MeasurementUnit.PERCENTAGE),
                width=(0.8, MeasurementUnit.PERCENTAGE),
                top=(0, MeasurementUnit.PIXELS),
                left=(0.2, MeasurementUnit.PERCENTAGE),
                title='Window 2',
            ),
            Example(
                stdscr=stdscr,
                height=(0.2, MeasurementUnit.PERCENTAGE),
                width=(1.0, MeasurementUnit.PERCENTAGE),
                top=(0.8, MeasurementUnit.PERCENTAGE),
                left=(0, MeasurementUnit.PIXELS),
                title='Window 3',
            ),
        ]

    

    def run(self, stdscr: curses.window):
        stdscr.keypad(True)
        stdscr.nodelay(True)
        self._draw_components()
        stdscr.refresh()
        while True:
            self._draw_components()
            key = stdscr.getch()
            if key == 81 or key == 113: # Q
                break
            elif key == 9: # TAB
                for _ in range(len(self.components)):
                    self.component_index += 1
                    if self.component_index >= len(self.components):
                        self.component_index = 0
                    if self.components[self.component_index].is_focusable:
                        break
            elif key == curses.KEY_RESIZE:
                stdscr.erase()                
                for component in self.components:
                    component.reset_window()
                stdscr.refresh()
            else:
                self.components[self.component_index].handle_key(key)

    def _draw_components(self):
        for index, component in enumerate(self.components):
            component.draw(index == self.component_index)

curses.wrapper(lambda stdscr: Body(stdscr).run(stdscr))