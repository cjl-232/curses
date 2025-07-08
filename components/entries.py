import curses

from states import State
from styling import Layout, Padding
from windows import ManagedWindow

class Entry(ManagedWindow):
    def __init__(
            self,
            layout: Layout,
            padding: Padding | None = None,
            title: str | None = None,
            footer: str | None = None,
            bordered: bool = False,
            focusable: bool = False,
        ) -> None:
        super().__init__(layout, padding, title, footer, bordered, focusable)
        self.input: str = ''
        self.cursor_index = 0

    def draw(self, focused: bool):
        # Set cursor visibility.
        curses.curs_set(1 if focused else 0)

        # Determine the space available for input, and halt if insufficient.
        height, width = self._get_internal_size()
        if height <= 0 or width <= 0:
            self.window.refresh()
            self.draw_required = False
            return
        
        # Draw the border.
        self._draw_external(focused)

        # Determine the number of rows required to display the full input.
        required_rows = len(self.input) // width

        # Determine the position of the cursor within the input.
        cursor_col = self.cursor_index % width
        cursor_row = self.cursor_index // width

        # Determine the visible part of the input.
        if cursor_row > required_rows - 1:
            first_row = cursor_row - (height - 1)
        elif cursor_row <= (required_rows - 1) - (height - 1):
            first_row = cursor_row
        else:
            first_row = required_rows - (height - 1)
        first_row = max(0, first_row)
        last_row = first_row + (height - 1)

        # Extract this from the actual input, padding as required.
        content = self.input[first_row * width:(last_row + 1) * width]
        if len(content) % width != 0:
            content += ' ' * (width - len(content) % width)
        if len(content) < height * width:
            left_padding = ' ' * (height * width - len(content))
            content += left_padding
        
        # Draw this to the window.
        for i in range(last_row - first_row + 1):
            self.window.addstr(
                i + self.padding.top + 1,
                1 + self.padding.left,
                content[i * width:(i + 1) * width],
            )

        # Position the cursor.
        self.window.move(
            cursor_row - first_row + self.padding.top + 1,
            cursor_col + 1 + self.padding.left,
        )

        # Refresh the window.
        self.window.refresh()
        self.draw_required = False
    
    def handle_key(self, key: int) -> State:
        height, width = self._get_internal_size()
        match key:
            case curses.KEY_UP:
                if self.cursor_index > 0:
                    self.cursor_index -= width
                    if self.cursor_index < 0:
                        self.cursor_index = 0
                    self.draw_required = True
            case curses.KEY_DOWN:
                if self.cursor_index < len(self.input):
                    self.cursor_index += width
                    if self.cursor_index > len(self.input):
                        self.cursor_index = len(self.input)
                    self.draw_required = True
            case curses.KEY_LEFT:
                if self.cursor_index > 0:
                    self.cursor_index -= 1
                    self.draw_required = True
            case curses.KEY_RIGHT:
                if self.cursor_index < len(self.input):
                    self.cursor_index += 1
                    self.draw_required = True
            case curses.KEY_HOME:
                if self.cursor_index > 0:
                    self.cursor_index = 0
                    self.draw_required = True
            case curses.KEY_END:
                if self.cursor_index < len(self.input):
                    self.cursor_index = len(self.input)
                    self.draw_required = True
            case curses.KEY_PPAGE:
                if self.cursor_index > 0:
                    self.cursor_index -= width * height
                    if self.cursor_index < 0:
                        self.cursor_index = 0
                    self.draw_required = True
            case curses.KEY_NPAGE:
                if self.cursor_index < len(self.input):
                    self.cursor_index += width * height
                    if self.cursor_index > len(self.input):
                        self.cursor_index = len(self.input)
                    self.draw_required = True
            case 8 | curses.KEY_BACKSPACE:
                if self.cursor_index > 0:
                    head = self.input[:self.cursor_index - 1]
                    tail = self.input[self.cursor_index:]
                    self.input = head + tail
                    self.cursor_index -= 1
                    self.draw_required = True
            case _:
                if 0 <= key <= 0x10ffff and chr(key).isascii():
                    if self.cursor_index == len(self.input):
                        self.input += chr(key)
                    else:
                        head = self.input[:self.cursor_index]
                        tail = self.input[self.cursor_index:]
                        self.input = head + chr(key) + tail
                    self.cursor_index += 1
                    self.draw_required = True
        return State.STANDARD