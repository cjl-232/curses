#TODO replace settings with cached... ideally also property?
#TODO figure this out... derive from prompts, get a result property that takes
# into account NUMERIC choices as well. Text prompt vs choice prompt.
# Implement as a enum in the PromptNode field?

import curses
import time

import httpx

from sqlalchemy import create_engine

from components.contacts import ContactsPrompt
from database.operations import store_fetched_data
from parser import ClientArgumentParser
from server.operations import fetch_data
from settings import settings  # This is causing slowdown. Adjust it.
from states import State
from windows import ManagedWindow

parser = ClientArgumentParser()

class App:
    def __init__(self, stdscr: curses.window, *windows: ManagedWindow):
        self.stdscr = stdscr
        self.engine = create_engine(settings.local_database.url)
        self.signature_key = parser.signature_key
        self.windows = list(windows)
        self.focus_index = 0

    def _fetch_handler(self):
        client = httpx.Client(timeout=settings.server.request_timeout)
        while True:
            response = fetch_data(self.engine, self.signature_key, client)
            if response is not None:
                store_fetched_data(self.engine, response)
            time.sleep(settings.server.fetch_interval)

    def _handle_key_standard(self, key: int) -> State:
        match key:
            case 9:   # Tab
                return State.NEXT_WINDOW
            case curses.KEY_BTAB:
                return State.PREV_WINDOW
            case curses.KEY_RESIZE:
                return State.RESIZE
            case 27:  # Esc
                return State.TERMINATE
            case _:
                return self.windows[self.focus_index].handle_key(key)

    def run(self):
        self.stdscr.keypad(True)
        self.stdscr.nodelay(True)
        self.stdscr.clear()
        self.stdscr.refresh()
        for window in self.windows:
            window.place(self.stdscr)
        state = State.STANDARD
        while self.windows and state != State.TERMINATE:
            match state:
                case State.STANDARD:
                    for index, window in enumerate(self.windows):
                        if window.draw_required:
                            window.draw(index == self.focus_index)
                    state = self._handle_key_standard(self.stdscr.getch())
                case State.NEXT_WINDOW:
                    for _ in range(len(self.windows)):
                        self.focus_index += 1
                        if self.focus_index >= len(self.windows):
                            self.focus_index = 0
                        if self.windows[self.focus_index].focusable:
                            break
                    state = State.STANDARD
                case State.PREV_WINDOW:
                    for _ in range(len(self.windows)):
                        self.focus_index -= 1
                        if self.focus_index < 0:
                            self.focus_index = len(self.windows) - 1
                        if self.windows[self.focus_index].focusable:
                            break
                    state = State.STANDARD
                case State.RESIZE:
                    self.stdscr.erase()
                    self.stdscr.refresh()
                    for window in self.windows:
                        window.place(self.stdscr)
                    state = State.STANDARD
                case State.ADD_CONTACT:
                    self.stdscr.erase()
                    self.stdscr.refresh()
                    state = State.PROMPT_ACTIVE
                    prompt = ContactsPrompt()
                    prompt.place(self.stdscr)
                    while state == State.PROMPT_ACTIVE:
                        if prompt.draw_required:
                            prompt.draw()
                            prompt.draw_required = False
                        key = self.stdscr.getch()
                        if key == curses.KEY_RESIZE:
                            prompt.place(self.stdscr)
                        else:
                            state = prompt.handle_key(key)
                    match state:
                        case State.PROMPT_SUBMITTED:
                            print(prompt.retrieve_contact())
                        case _:
                            pass
                    self.stdscr.erase()
                    self.stdscr.refresh()
                    for window in self.windows:
                        window.draw_required = True
                    state = State.STANDARD
                case _:
                    state = State.STANDARD

            

from styling import (
    Layout,
    LayoutMeasure,
    LayoutUnit,
    Padding,
)
from components.contacts import ContactsMenu



if __name__ == '__main__':
    def main(stdscr: curses.window):
        app = App(stdscr)
        app.windows.append(
            ContactsMenu(
                engine=app.engine,
                layout=Layout(
                    height=LayoutMeasure(
                        (80, LayoutUnit.PERCENTAGE),
                    ),
                    width=LayoutMeasure(
                        (20, LayoutUnit.PERCENTAGE),
                    ),
                    top=LayoutMeasure(),
                    left=LayoutMeasure(),
                ),
                padding=Padding(1),
            )
        )
        app.run()
    curses.wrapper(main)