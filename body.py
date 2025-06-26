import curses

from components.base import ComponentWindow

class Example(ComponentWindow):
    def draw(self):
        """Draw the window on the terminal. Always begin by erasing."""
        self._window.erase()
        if self._bordered:
            if self._focused:
                self._window.attron(curses.A_BOLD)
                self._window.box()
                self._window.attroff(curses.A_BOLD)
            else:
                self._window.box()
        self._window.refresh()


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
        self.components[0].set_focused(True)

    

    def run(self, stdscr: curses.window):
        stdscr.keypad(True)
        while True:
            for component in self.components:
                component.draw()
            key = stdscr.getch()
            if key == 81 or key == 113: # Q
                break
            elif key == 9: # TAB
                self.components[self.component_index].set_focused(False)
                while True:
                    self.component_index += 1
                    if self.component_index >= len(self.components):
                        self.component_index = 0
                    if self.components[self.component_index].is_focusable:
                        break
                self.components[self.component_index].set_focused(True)

curses.wrapper(lambda stdscr: Body().run(stdscr))