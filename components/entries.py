import abc
import curses

from components.base import ComponentWindow, Measurement

class Entry(ComponentWindow, metaclass=abc.ABCMeta):
    def __init__(
            self,
            stdscr: curses.window,
            height: Measurement,
            width: Measurement,
            top: Measurement,
            left: Measurement,
            title: str | None = None,
        ):
        super().__init__(
            stdscr=stdscr,
            height=height,
            width=width,
            top=top,
            left=left,
            title=title,
            focusable=True,
        )
        self._input: str = ''
        self._cursor_index = 0

    def draw(self, focused: bool):
        # Clear the window.
        self._window.clear()

        # Set cursor visibility.
        curses.curs_set(1 if focused else 0)

        # Determine the space available for input, and halt if insufficient.
        height, width = (x - 2 for x in self._window.getmaxyx())
        if height <= 0 or width <= 0:
            self._window.refresh()
            self.draw_required = False
            return
        
        # Draw the border.
        self._draw_border(focused)

        # Determine the number of rows required to display the full input.
        required_rows = len(self._input) // width

        # Ensure the cursor is at a valid position.
        if self._cursor_index < 0:
            self._cursor_index = 0
        elif self._cursor_index > len(self._input):
            self._cursor_index = len(self._input)

        # Determine the position of the cursor within the input.
        cursor_col = self._cursor_index % width
        cursor_row = self._cursor_index // width

        # Determine the visible part of the input.
        if cursor_row > required_rows - 1:
            first_row = cursor_row - (height - 1)
        elif cursor_row <= (required_rows - 1) - (height - 1):
            first_row = cursor_row
        else:
            first_row = (required_rows - 1) - (height - 1)
        last_row = first_row + (height - 1)

        # Extract this from the actual input, padding as required.
        content = self._input[first_row * width:last_row * width]
        if len(content) % width != 0:
            content += ' ' * (width - len(content) % width)
        if len(content) < height * width:
            left_padding = ' ' * (height * width - len(content))
            content += left_padding
        
        # Draw this to the window.
        for i in range(last_row - first_row + 1):
            self._window.addstr(i + 1, 1, content[i * width:(i + 1) * width])

        # Position the cursor.
        self._window.move(cursor_row - first_row, 1 + cursor_col)

        # Refresh the window.
        self._window.refresh()
        self.draw_required = False



        

        

