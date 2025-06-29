import abc
import curses
import math

from components.base import ComponentWindow, Measurement
from settings import settings

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
        self._items = items
        self._cursor_index: int = 0

    def draw(self, focused: bool):
        # Erase the window and redraw the border.
        self._window.erase()
        self._draw_border(focused)

        # Hide the cursor and enable the keypad.
        #curses.curs_set(0)
        self._window.keypad(True)

        # Determine the number of rows available.
        height, width = self._get_internal_size()
        items_per_page = height - 1
        
        # Work out the current cursor position.
        page_count = math.ceil(len(self._items) / items_per_page)
        current_page_index = self._cursor_index // items_per_page 
        relative_cursor_index = self._cursor_index % items_per_page

        # Extract the relevant items.
        start = current_page_index * items_per_page
        stop = start + items_per_page
        page_items = self._items[start:stop]

        # Render the menu.
        x_pos = 1 + settings.display.left_padding
        y_pos = 1 + settings.display.top_padding
        for index, item in enumerate(page_items):
            if index == relative_cursor_index and focused:
                self._window.attron(curses.A_REVERSE)
                self._window.addnstr(y_pos + index, x_pos, item, width)
                self._window.attroff(curses.A_REVERSE)
            else:
                self._window.addnstr(y_pos + index, x_pos, item, width)
        page_label = f'Page {current_page_index + 1} of {page_count}'
        self._window.attron(curses.A_ITALIC)
        self._window.addstr(y_pos + items_per_page, x_pos, page_label)
        self._window.attroff(curses.A_ITALIC)

        # Refresh the window.
        self._window.refresh()
        self.draw_required = False

    def handle_key(self, key: int):
        items_per_page = self._get_internal_size()[0] - 1
        page_count = math.ceil(len(self._items) / items_per_page)
        last_page_index = items_per_page * (page_count - 1)
        relative_cursor_index = self._cursor_index % items_per_page
        if key in settings.key_bindings.up_key_set:
            if relative_cursor_index != 0:
                self._cursor_index -= 1
                if self._cursor_index < 0:
                    self._cursor_index = len(self._items) - 1
            else:
                self._cursor_index += items_per_page - 1
                if self._cursor_index >= len(self._items):
                    self._cursor_index = len(self._items) - 1
            self.draw_required = True
        elif key in settings.key_bindings.down_key_set:
            if relative_cursor_index != items_per_page - 1:
                self._cursor_index += 1
                if self._cursor_index >= len(self._items):
                    self._cursor_index = 0
            else:
                self._cursor_index = 0
            self.draw_required = True
        elif key in settings.key_bindings.left_key_set:
            self._cursor_index -= items_per_page
            if self._cursor_index < 0:
                self._cursor_index = last_page_index + relative_cursor_index
                if self._cursor_index >= len(self._items):
                    self._cursor_index = len(self._items) - 1
            self.draw_required = True
        elif key in settings.key_bindings.right_key_set:
            self._cursor_index += items_per_page
            if self._cursor_index >= len(self._items):
                if self._cursor_index - items_per_page >= last_page_index:
                    self._cursor_index = relative_cursor_index
                else:
                    self._cursor_index = len(self._items) - 1
            self.draw_required = True
        elif key == curses.KEY_HOME and self._cursor_index != 0:
            self._cursor_index = 0
            self.draw_required = True
        elif key == curses.KEY_END:
            if self._cursor_index != len(self._items) - 1:
                self._cursor_index = len(self._items) - 1
                self.draw_required = True