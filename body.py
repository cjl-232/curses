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
            Example(10, 10),
            Example(10, 10, 10, 10),
            Example(10, 20, 0, 20),
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

curses.wrapper(lambda stdscr: Body().run(stdscr))