import curses

from components.base import ComponentWindow

class Example(ComponentWindow):
    def draw(self):
        """Draw the window on the terminal. Always begin by erasing."""

    def handle_key(self, key: int):
        """Handle key presses when this window is active."""

class Body:
    def __init__(self):
        self.component_index = 0
        self.components: list[ComponentWindow] = [
            Example(100, 100),
            Example(100, 100, 100, 100),
            Example(100, 200, 0, 200),
        ]

    def run(self, stdscr: curses.window):
        stdscr.keypad(True)
        while True:
            key = stdscr.getch()
            if key == 81 or key == 113: # Q
                break
            elif key == 9: # TAB
                while True:
                    self.component_index += 1
                    if self.component_index >= len(self.components):
                        self.component_index = 0
                    if self.components[self.component_index].is_focusable:
                        break

body = Body()
curses.wrapper(body.run)