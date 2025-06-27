import abc
import curses
import math

from typing import Callable

from components.base import ComponentWindow, Measurement
from settings import settings

type _KeyPressDict = dict[int, Callable[[curses.window], None]]

class PaginatedMenu(ComponentWindow, metaclass=abc.ABCMeta):
    def __init__(
            self,
            items: list[str],
            stdscr: curses.window,
            height: Measurement,
            width: Measurement,
            top: Measurement,
            left: Measurement,
            title: str | None = None,
            focusable: bool = True,
        ):
        super().__init__(stdscr, height, width, top, left, title, focusable)
        if not items:
            raise ValueError('Empty menus are not allowed.')
        self.items = items
        self.cursor_index: int = 0

    def draw(self, focused: bool):
        # Erase the window and redraw the border.
        self._window.erase()
        self._draw_border(focused)

        # Hide the cursor and enable the keypad.
        curses.curs_set(0)
        self._window.keypad(True)

        # Determine the number of rows available.
        height, width = self._window.getmaxyx()
        items_per_page = height - 3
        
        # Work out the current cursor position.
        page_count = math.ceil(len(self.items) / items_per_page)
        current_page_index = self.cursor_index // items_per_page 
        relative_cursor_index = self.cursor_index % items_per_page

        # Extract the relevant items.
        start = current_page_index * items_per_page
        stop = start + items_per_page
        page_items = self.items[start:stop]

        # Render the menu.
        for index, item in enumerate(page_items):
            if index == relative_cursor_index:
                self._window.attron(curses.A_REVERSE)
                self._window.addnstr(1 + index, 1, item, width - 2)
                self._window.attroff(curses.A_REVERSE)
            else:
                self._window.addnstr(1 + index, 1, item, width - 2)
        page_label = f'Page {current_page_index + 1} of {page_count}'
        self._window.addstr(height - 2, 1, page_label, curses.A_ITALIC)

        # Refresh the window.
        self._window.refresh()
        self.draw_required = False

    def handle_key(self, key: int):
        if key in settings.key_bindings.up_key_set:
            self.cursor_index -= 1
            if self.cursor_index < 0:
                self.cursor_index = len(self.items) - 1
            self.draw_required = True
        elif key in settings.key_bindings.down_key_set:
            self.cursor_index += 1
            if self.cursor_index >= len(self.items):
                self.cursor_index = 0
            self.draw_required = True
        elif key in settings.key_bindings.left_key_set:
            items_per_page = self._window.getmaxyx()[0] - 3
            page_count = math.ceil(len(self.items) / items_per_page)
            last_page_index = items_per_page * (page_count - 1)
            relative_cursor_index = self.cursor_index % items_per_page
            self.cursor_index -= items_per_page
            if self.cursor_index < 0:
                self.cursor_index = last_page_index + relative_cursor_index
                if self.cursor_index >= len(self.items):
                    self.cursor_index = len(self.items) - 1
            self.draw_required = True
        elif key in settings.key_bindings.right_key_set:
            items_per_page = self._window.getmaxyx()[0] - 3
            page_count = math.ceil(len(self.items) / items_per_page)
            last_page_index = items_per_page * (page_count - 1)
            relative_cursor_index = self.cursor_index % items_per_page
            self.cursor_index += items_per_page
            if self.cursor_index >= len(self.items):
                if self.cursor_index - items_per_page >= last_page_index:
                    self.cursor_index = relative_cursor_index
                else:
                    self.cursor_index = len(self.items) - 1
            self.draw_required = True
        elif key == curses.KEY_HOME and self.cursor_index != 0:
            self.cursor_index = 0
            self.draw_required = True
        elif key == curses.KEY_END and self.cursor_index < len(self.items) - 1:
            self.cursor_index = len(self.items) - 1
            self.draw_required = True