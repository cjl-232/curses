import abc
import curses
import math

from typing import Callable

from components.base import Component
from settings import settings

type _KeyPressDict = dict[int, Callable[[curses.window], None]]

class PaginatedMenu(Component, metaclass=abc.ABCMeta):
    def __init__(
            self,
            title: str,
            items: list[str],
            break_after_action: bool = False,
            additional_key_mappings: _KeyPressDict | None = None
        ):
        self.title = title
        if not items:
            raise ValueError('Empty menus are not allowed.')
        self.items = items
        self.break_after_action = break_after_action
        if additional_key_mappings is None:
            additional_key_mappings = {}
        self.additional_key_mappings = additional_key_mappings
        self.cursor_index = 0

    def run(self, stdscr: curses.window):
        # Set up persistent variables and begin the loop.
        while True:
            # Clear the screen and set properties each iteration.
            stdscr.clear()
            curses.curs_set(0)
            stdscr.nodelay(settings.display.await_inputs == False)

            # Extract height information, and enforce a minimum.
            height = stdscr.getmaxyx()[0]
            if height < 3:
                stdscr.addstr(0, 0, 'Insufficient terminal height.')
                stdscr.refresh()
                continue
            else:
                stdscr.addstr(0, 0, ' ' * len('Insufficient terminal height.'))

            # Work out the count and size of each page.
            items_per_page = min(height - 2, settings.display.max_page_height)
            page_count = math.ceil(len(self.items) / items_per_page)

            # Use the page size to work out the current cursor position.
            current_page_index = self.cursor_index // items_per_page 
            relative_cursor_index = self.cursor_index % items_per_page

            # Extract the relevant items.
            start = current_page_index * items_per_page
            stop = start + items_per_page
            page_items = self.items[start:stop]

            # Render the menu.
            top_pos = height - items_per_page - 2
            stdscr.attron(curses.A_BOLD)
            stdscr.attron(curses.A_UNDERLINE)
            stdscr.addstr(top_pos, 0, self.title)
            stdscr.attroff(curses.A_BOLD)
            stdscr.attroff(curses.A_UNDERLINE)
            for index, item in enumerate(page_items):
                if index == relative_cursor_index:
                    stdscr.attron(curses.A_REVERSE)
                    stdscr.addstr(top_pos + 1 + index, 0, item)
                    stdscr.attroff(curses.A_REVERSE)
                else:
                    stdscr.addstr(top_pos + 1 + index, 0, item)
            page_label = f'Page {current_page_index + 1} of {page_count}'
            stdscr.attron(curses.A_ITALIC)
            stdscr.addstr(height - 1, 0, page_label)
            stdscr.attroff(curses.A_ITALIC)
            stdscr.refresh()

            # Handle user input.
            key = stdscr.getch()
            match key:
                case curses.KEY_UP:
                    self.cursor_index -= 1
                    if self.cursor_index < 0:
                        self.cursor_index = len(self.items) - 1
                case curses.KEY_DOWN:
                    self.cursor_index += 1
                    if self.cursor_index >= len(self.items):
                        self.cursor_index = 0
                case curses.KEY_LEFT:
                    self.cursor_index -= items_per_page
                    if self.cursor_index < 0:
                        self.cursor_index += page_count * items_per_page
                        if self.cursor_index >= len(self.items):
                            self.cursor_index = len(self.items) - 1
                case curses.KEY_RIGHT:
                    self.cursor_index += items_per_page
                    if self.cursor_index >= len(self.items):
                        if current_page_index == page_count - 1:
                            self.cursor_index = relative_cursor_index
                        else:
                            self.cursor_index = len(self.items) - 1
                case 10: # Enter
                    self.handle_selection(stdscr, self.cursor_index)
                    if self.break_after_action:
                        break
                case 27: # Escape
                    break
                case _:
                    if key in self.additional_key_mappings:
                        self.additional_key_mappings[key](stdscr)
                        if self.break_after_action:
                            break

    @abc.abstractmethod
    def handle_selection(self, stdscr: curses.window, cursor_index: int):
        """Handle a menu option being selected."""

if __name__ == '__main__':
    from names import get_full_name
    class TestMenu(PaginatedMenu):
        def __init__(self, title: str, contacts: list[str]):
            super().__init__(
                title=title,
                items=contacts,
                break_after_action=False,
                additional_key_mappings={
                    curses.KEY_F10: self.key_handler,
                },
            )
        def handle_selection(self, stdscr: curses.window, cursor_index: int):
            raise ValueError(self.items[cursor_index])
        
        def key_handler(self, _: curses.window):
            print('Pressed F10')
    
    curses.wrapper(TestMenu(title='Contacts', contacts=[get_full_name() for _ in range(40)]).run)