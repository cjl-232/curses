import curses

from components.base import Component
from database.outputs.schemas import ContactOutputSchema

class MessagesScreen(Component):
    def __init__(self, contact: ContactOutputSchema):
        self.contact = contact

    def run(self, stdscr: curses.window):
        stdscr.nodelay(False)
        stdscr.clear()
        stdscr.addstr(stdscr.getmaxyx()[0] - 1, 0, f'This will be used for messaging {self.contact.name}. Please press enter to go back.')
        stdscr.refresh()
        while stdscr.getch() != 10:
            pass
