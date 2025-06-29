import curses
import textwrap

from datetime import datetime

from components.base import ComponentWindow, Measurement
from settings import settings

class Log(ComponentWindow):
    def __init__(
            self,
            stdscr: curses.window,
            height: Measurement,
            width: Measurement,
            top: Measurement,
            left: Measurement,
            title: str | None,
        ):
        super().__init__(
            stdscr=stdscr,
            height=height,
            width=width,
            top=top,
            left=left,
            title=title,
        )
        self._scroll_index: int = 0 # Scroll upwards
        self._item_lines: list[tuple[str, bool]] = list()

    def draw(self, focused: bool):
        self._window.erase()
        self._draw_border(focused)
        height, width = (x - 2 for x in self._window.getmaxyx())
        if height <= 0 or width <= 0:
            self._window.refresh()
            self.draw_required = False
            return
        if self._scroll_index == 0:
            visible_lines = self._item_lines[-height:]
        else:
            start = 0 - height - self._scroll_index
            stop = -self._scroll_index
            visible_lines = self._item_lines[start:stop]
        for index, (line, header) in enumerate(visible_lines):
            if header:
                self._window.attron(curses.A_BOLD)
                self._window.addnstr(index + 1, 1, line, width)
                self._window.attroff(curses.A_BOLD)
            else:
                self._window.addnstr(index + 1, 1, line, width)
        self._window.refresh()
        self.draw_required = False

    def handle_key(self, key: int):
        height = self._window.getmaxyx()[0] - 2
        if key in settings.key_bindings.up_key_set:
            self._scroll_index += 1
            if self._scroll_index >= len(self._item_lines) - height:
                self._scroll_index = len(self._item_lines) - 1 - height
            self.draw_required = True
        elif key in settings.key_bindings.down_key_set:
            if self._scroll_index > 0:
                self._scroll_index -= 1
                self.draw_required = True

    def add_item(
            self,
            text: str,
            title: str | None = None,
            timestamp: datetime | None = None,
    ):
        width = self._window.getmaxyx()[1] - 2
        if width > 0:
            return
        wrapped_text = textwrap.wrap(text, width, drop_whitespace=False)
        if not wrapped_text:
            return
        header = ''
        if title is not None:
            header += title
        if timestamp is not None:
            header += ' ' * (width - len(header) - 16)
            header += timestamp.strftime('%Y-%m-%d %H:%M')
        if header:
            self._item_lines += [(header, True)]
        self._item_lines += [(x, False) for x in wrapped_text]