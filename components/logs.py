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
            title: str | None = None,
            bordered: bool = True,
        ):
        super().__init__(
            stdscr=stdscr,
            height=height,
            width=width,
            top=top,
            left=left,
            title=title,
            bordered=bordered,
        )
        self._scroll_index: int = 0 # Scroll upwards
        self._items: list[tuple[str, str | None, datetime | None]] = list()
        self._item_lines: list[tuple[str, bool]] = list()

    def draw(self, focused: bool):
        self._window.erase()
        self._draw_border(focused)
        height, width = self._get_internal_size()
        if height <= 0 or width <= 0:
            self._window.refresh()
            self.draw_required = False
            return
        if self._scroll_index == 0:
            visible_lines = self._item_lines[-height:]
        else:
            start = 0 - height - self._scroll_index
            stop = start + height
            visible_lines = self._item_lines[start:stop]
        x_pos = 1 + settings.display.left_padding
        for index, (line, header) in enumerate(reversed(visible_lines)):
            if header:
                self._window.attron(curses.A_BOLD)
                self._window.addnstr(
                    height + settings.display.bottom_padding - index,
                    x_pos,
                    line,
                    width,
                )
                self._window.attroff(curses.A_BOLD)
            else:
                self._window.addnstr(
                    height + settings.display.bottom_padding - index,
                    x_pos,
                    line,
                    width,
                )
        self._window.refresh()
        self.draw_required = False

    def handle_key(self, key: int):
        height = self._get_internal_size()[0]
        if key in settings.key_bindings.up_key_set:
            if self._scroll_index < len(self._item_lines) - height:
                self._scroll_index += 1
                self.draw_required = True
        elif key in settings.key_bindings.down_key_set:
            if self._scroll_index > 0:
                self._scroll_index -= 1
                self.draw_required = True

    def add_item(
            self,
            text: str,
            cached: bool,
            title: str | None = None,
            timestamp: datetime | None = None,
    ):
        width = self._get_internal_size()[1]
        if width <= 0:
            return
        wrapped_text = textwrap.wrap(text, width)
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
            if self._scroll_index != 0:
                self._scroll_index += 1
        if not cached:
            self._items.append((text, title, timestamp))
        self._item_lines += [(x, False) for x in wrapped_text]
        if self._scroll_index != 0:
            self._scroll_index += len(wrapped_text)
        self.draw_required = True

    def reset_window(self):
        super().reset_window()
        self._item_lines.clear()
        self._scroll_index = 0
        for (text, title, timestamp) in self._items:
            self.add_item(text, True, title, timestamp)