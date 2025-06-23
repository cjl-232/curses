import curses

from components.base import Component

class Prompt(Component):
    def __init__(self, message: str):
        self.entry = ''
        self.errors: list[str] = []
        self.message = message
        self.cancelled = False

    def run(self, stdscr: curses.window):
        while True:
            stdscr.clear()
            stdscr.nodelay(False)
            height = stdscr.getmaxyx()[0]
            y_pos = height - 1
            stdscr.move(y_pos, len(self.entry))
            stdscr.addstr(y_pos, 0, self.entry)
            y_pos -= 1
            stdscr.addstr(y_pos, 0, self.message)
            for error in self.errors[::-1]:
                y_pos -= 1
                stdscr.addstr(y_pos, 0, error)
            stdscr.refresh()
            key = stdscr.getch()
            if key == 8 and self.entry:
                self.entry = self.entry[:-1]
            elif key == 10:
                return
            elif key == 27:
                self.cancelled = True
                return
            elif chr(key).isprintable():
                self.entry += chr(key)