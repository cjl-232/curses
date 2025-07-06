import abc
import curses
import math

from settings import settings
from states import State
from styling import Layout, Padding
from windows import ManagedWindow

class PaginatedMenu(ManagedWindow, metaclass=abc.ABCMeta):
    def __init__(
            self,
            items: list[str],
            layout: Layout,
            padding: Padding | None = None,
            title: str | None = None,
            footer: str | None = None,
        ) -> None:
        super().__init__(layout, padding, title, footer, True, True)
        self.items = items
        self.cursor_index = 0

    def draw(self, focused: bool):
        # Erase the window and redraw the border.
        self.window.erase()

        # Hide the cursor and enable the keypad.
        curses.curs_set(0)
        self.window.keypad(True)

        # Determine the number of rows available.
        height, width = self._get_internal_size()
        items_per_page = height - 1

        # Terminate if space is insufficient.
        if height <= 1 or width <= 0:
            self.window.refresh()
            return
        
        # Otherwise, draw the border.
        self._draw_external(focused)
        
        # Work out the current cursor position.
        page_count = math.ceil(len(self.items) / items_per_page)
        current_page_index = self.cursor_index // items_per_page 
        relative_cursor_index = self.cursor_index % items_per_page

        # Extract the relevant items.
        start = current_page_index * items_per_page
        stop = start + items_per_page
        page_items = self.items[start:stop]

        # Render the menu.
        y_pos = self.padding.top + 1
        x_pos = self.padding.left + 1
        for index, item in enumerate(page_items):
            if index == relative_cursor_index and focused:
                self.window.attron(curses.A_REVERSE)
                self.window.addnstr(y_pos + index, x_pos, item, width)
                self.window.attroff(curses.A_REVERSE)
            else:
                self.window.addnstr(y_pos + index, x_pos, item, width)
        page_label = f'Page {current_page_index + 1} of {page_count}'
        self.window.attron(curses.A_ITALIC)
        self.window.addnstr(y_pos + items_per_page, x_pos, page_label, width)
        self.window.attroff(curses.A_ITALIC)

        # Refresh the window.
        self.window.refresh()

    def handle_key(self, key: int) -> State:
        items_per_page = self._get_internal_size()[0] - 1
        if items_per_page <= 0:
            return State.STANDARD
        page_count = math.ceil(len(self.items) / items_per_page)
        last_page_index = items_per_page * (page_count - 1)
        relative_cursor_index = self.cursor_index % items_per_page
        if key in settings.key_bindings.up_key_set:
            if relative_cursor_index != 0:
                self.cursor_index -= 1
                if self.cursor_index < 0:
                    self.cursor_index = len(self.items) - 1
            else:
                self.cursor_index += items_per_page - 1
                if self.cursor_index >= len(self.items):
                    self.cursor_index = len(self.items) - 1
            self.draw_required = True
        elif key in settings.key_bindings.down_key_set:
            if relative_cursor_index != items_per_page - 1:
                self.cursor_index += 1
                if self.cursor_index >= len(self.items):
                    self.cursor_index = 0
            else:
                self.cursor_index = 0
            self.draw_required = True
        elif key in settings.key_bindings.left_key_set:
            self.cursor_index -= items_per_page
            if self.cursor_index < 0:
                self.cursor_index = last_page_index + relative_cursor_index
                if self.cursor_index >= len(self.items):
                    self.cursor_index = len(self.items) - 1
            self.draw_required = True
        elif key in settings.key_bindings.right_key_set:
            self.cursor_index += items_per_page
            if self.cursor_index >= len(self.items):
                if self.cursor_index - items_per_page >= last_page_index:
                    self.cursor_index %= items_per_page
                else:
                    self.cursor_index = len(self.items) - 1
            self.draw_required = True
        elif key == curses.KEY_HOME and self.cursor_index != 0:
            self.cursor_index = 0
            self.draw_required = True
        elif key == curses.KEY_END:
            if self.cursor_index != len(self.items) - 1:
                self.cursor_index = len(self.items) - 1
                self.draw_required = True
        elif key == 1:
            return State.ADD_CONTACT
        return State.STANDARD