import curses
import textwrap

from datetime import datetime

from settings import settings
from states import State
from styling import Layout, Padding
from windows import ManagedWindow

class Log(ManagedWindow):
    def __init__(
            self,
            layout: Layout,
            padding: Padding | None = None,
            title: str | None = None,
            footer: str | None = None,
            bordered: bool = True,
            focusable: bool = True,
        ):
        super().__init__(layout, padding, title, footer, bordered, focusable)
        self.scroll_index: int = 0 # Scroll upwards
        self.items: list[tuple[str, str | None, datetime | None]] = list()
        self.item_lines: list[tuple[str, bool]] = list()

    def draw(self, focused: bool):
        self.window.erase()
        self._draw_external(focused)
        height, width = self._get_internal_size()
        if height <= 0 or width <= 0:
            self.window.refresh()
            self.draw_required = False
            return
        if self.scroll_index == 0:
            visible_lines = self.item_lines[-height:]
        else:
            start = 0 - height - self.scroll_index
            stop = start + height
            visible_lines = self.item_lines[start:stop]
        x_pos = 1 + self.padding.left
        for index, (line, header) in enumerate(reversed(visible_lines)):
            y_pos = height + self.padding.bottom - index
            if header:
                self.window.attron(curses.A_BOLD)
                self.window.addnstr(y_pos, x_pos, line, width)
                self.window.attroff(curses.A_BOLD)
            else:
                self.window.addnstr(y_pos, x_pos, line, width)
        self.window.refresh()
        self.draw_required = False

    def handle_key(self, key: int) -> State:
        height = self._get_internal_size()[0]
        if key in settings.key_bindings.up_key_set:
            if self.scroll_index < len(self.item_lines) - height:
                self.scroll_index += 1
                self.draw_required = True
        elif key in settings.key_bindings.down_key_set:
            if self.scroll_index > 0:
                self.scroll_index -= 1
                self.draw_required = True
        return State.STANDARD

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
            self.item_lines += [(header, True)]
            if self.scroll_index != 0:
                self.scroll_index += 1
        if not cached:
            self.items.append((text, title, timestamp))
        self.item_lines += [(x, False) for x in wrapped_text]
        if self.scroll_index != 0:
            self.scroll_index += len(wrapped_text)
        self.draw_required = True

    def place(self, stdscr: curses.window):
        super().place(stdscr)
        height = self._get_internal_size()[0]
        self.item_lines.clear()
        for (text, title, timestamp) in self.items:
            self.add_item(text, True, title, timestamp)
        if self.scroll_index > len(self.item_lines) - height:
            self.scroll_index = len(self.item_lines) - height