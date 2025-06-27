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
        self.cursor_index = 0

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

    def handle_key(self, key: int):
        if key in settings.key_bindings.up_key_set:
            self.cursor_index -= 1
            if self.cursor_index < 0:
                self.cursor_index = len(self.items) - 1
        elif key in settings.key_bindings.down_key_set:
            self.cursor_index += 1
            if self.cursor_index >= len(self.items):
                self.cursor_index = 0


    # def run(self, stdscr: curses.window):
    #     # Set up persistent variables and begin the loop.
    #     while True:
    #         # Clear the screen and set properties each iteration.
    #         stdscr.clear()
    #         curses.curs_set(0)
    #         stdscr.nodelay(settings.display.await_inputs == False)

    #         # Extract height information, and enforce a minimum.
    #         height = stdscr.getmaxyx()[0]
    #         if height < 5:
    #             continue

    #         # Work out the count and size of each page.
    #         #items_per_page = min(height - 4, settings.display.max_page_height)
    #         items_per_page = height - 4
    #         page_count = math.ceil(len(self.items) / items_per_page)

    #         # Use the page size to work out the current cursor position.
    #         current_page_index = self.cursor_index // items_per_page 
    #         relative_cursor_index = self.cursor_index % items_per_page

    #         # Extract the relevant items.
    #         start = current_page_index * items_per_page
    #         stop = start + items_per_page
    #         page_items = self.items[start:stop]

    #         # Render the menu.
    #         try:
    #             stdscr.attron(curses.A_BOLD)
    #             stdscr.attron(curses.A_UNDERLINE)
    #             stdscr.addstr(1, 1, self.title)
    #             stdscr.attroff(curses.A_BOLD)
    #             stdscr.attroff(curses.A_UNDERLINE)
    #             for index, item in enumerate(page_items):
    #                 if index == relative_cursor_index:
    #                     stdscr.attron(curses.A_REVERSE)
    #                     stdscr.addstr(2 + index, 1, item)
    #                     stdscr.attroff(curses.A_REVERSE)
    #                 else:
    #                     stdscr.addstr(2 + index, 1, item)
    #             page_label = f'Page {current_page_index + 1} of {page_count}'
    #             stdscr.attron(curses.A_ITALIC)
    #             stdscr.addstr(height - 2, 1, page_label)
    #             stdscr.attroff(curses.A_ITALIC)
    #             stdscr.border()
    #         except curses.error:
    #             continue
    #         stdscr.refresh()

    #         # Handle user input.
    #         key = stdscr.getch()
    #         bindings = settings.key_bindings
    #         if key == curses.KEY_UP or key in bindings.up_key_set:
    #             self.cursor_index -= 1
    #             if self.cursor_index < 0:
    #                 self.cursor_index = len(self.items) - 1
    #         elif key == curses.KEY_DOWN or key in bindings.down_key_set:
    #             self.cursor_index += 1
    #             if self.cursor_index >= len(self.items):
    #                 self.cursor_index = 0
    #         elif key == curses.KEY_LEFT or key in bindings.left_key_set:
    #             self.cursor_index -= items_per_page
    #             if self.cursor_index < 0:
    #                 self.cursor_index += page_count * items_per_page
    #                 if self.cursor_index >= len(self.items):
    #                     self.cursor_index = len(self.items) - 1
    #         elif key == curses.KEY_RIGHT or key in bindings.right_key_set:
    #             self.cursor_index += items_per_page
    #             if self.cursor_index >= len(self.items):
    #                 if current_page_index == page_count - 1:
    #                     self.cursor_index = relative_cursor_index
    #                 else:
    #                     self.cursor_index = len(self.items) - 1
    #         elif key == curses.KEY_ENTER or key == ord('\n'):
    #             self.handle_selection(stdscr, self.cursor_index)
    #             if self.break_after_action:
    #                 break
    #         elif key in self.additional_key_mappings:
    #             self.additional_key_mappings[key](stdscr)
    #             if self.break_after_action:
    #                 break

    # @abc.abstractmethod
    # def handle_selection(self, stdscr: curses.window, cursor_index: int):
    #     """Handle a menu option being selected."""