import abc
import curses
import math

from components.base import Component
from settings import settings

class Menu(Component, metaclass=abc.ABCMeta):
    def __init__(
            self,
            title: str,
            items: list[str],
            break_after_selection: bool = False,
        ):
        self.title = title
        if not items:
            raise ValueError('Empty menus are not allowed.')
        self.items = items
        self.break_after_selection = break_after_selection

    def run(self, stdscr: curses.window):
        # Set up persistent variables and begin the loop.
        cursor_index = 0
        while True:
            # Clear the screen and set properties each iteration.
            stdscr.clear()
            curses.curs_set(0)
            stdscr.nodelay(True)

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
            current_page_index = cursor_index // items_per_page 
            relative_cursor_index = cursor_index % items_per_page

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
            match stdscr.getch():
                case curses.KEY_UP:
                    cursor_index -= 1
                    if cursor_index < 0:
                        cursor_index = len(self.items) - 1
                case curses.KEY_DOWN:
                    cursor_index += 1
                    if cursor_index >= len(self.items):
                        cursor_index = 0
                case curses.KEY_LEFT:
                    cursor_index -= items_per_page
                    if cursor_index < 0:
                        cursor_index += page_count * items_per_page
                        if cursor_index >= len(self.items):
                            cursor_index = len(self.items) - 1
                case curses.KEY_RIGHT:
                    cursor_index += items_per_page
                    if cursor_index >= len(self.items):
                        if current_page_index == page_count - 1:
                            cursor_index = relative_cursor_index
                        else:
                            cursor_index = len(self.items) - 1
                case 10: # Enter
                    self.handle_selection(stdscr, cursor_index)
                    if self.break_after_selection:
                        break
                case 27: # Escape
                    break
                case _:
                    pass

    @abc.abstractmethod
    def handle_selection(self, stdscr: curses.window, cursor_index: int):
        """Handle a menu option being selected."""

if __name__ == '__main__':
    from names import get_full_name
    class TestMenu(Menu):
        def handle_selection(self, stdscr: curses.window, cursor_index: int):
            raise ValueError(self.items[cursor_index])
    
    curses.wrapper(TestMenu(title='Contacts', items=[get_full_name() for _ in range(40)]).run)