import abc
import binascii
import curses

from base64 import urlsafe_b64decode

from components.base import Component

class Prompt(Component, metaclass=abc.ABCMeta):
    def __init__(self, message: str):
        self.message = message
        self.errors: list[str] = list()
        self.cancelled = False

class ChoicePrompt(Prompt):
    def __init__(self, message: str, choices: list[str]):
        super().__init__(message)
        if len(choices) == 0:
            raise ValueError('At least one choice is required per prompt.')
        elif len(choices) > 9:
            raise ValueError('No more than 9 choices are allowed per prompt.')
        self.choices = choices

    def run(self, stdscr: curses.window) -> int | None:
        stdscr.nodelay(False)
        while True:
            stdscr.clear()
            height = stdscr.getmaxyx()[0]
            if height < len(self.choices) + 1:
                stdscr.addstr(height - 1, 0, 'Insufficient terminal height.')
                stdscr.refresh()
                continue
            top = height - 1 - len(self.choices)
            stdscr.addstr(top, 0, self.message)
            for idx, choice in enumerate(self.choices):
                stdscr.addstr(top + 1 + idx, 0, f'{idx + 1}. {choice}')
            stdscr.refresh()
            key = stdscr.getch()
            if 49 <= key < 49 + len(self.choices):
                return int(chr(key))
            elif key == 27:
                return None






class InputPrompt(Prompt):
    def __init__(self, message: str):
        super().__init__(message)
        self.entry = ''

    def run(self, stdscr: curses.window) -> str | None:
        while True:
            stdscr.clear()
            stdscr.nodelay(True)
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
            if key == -1:
                pass
            elif key == 8 and self.entry:
                self.entry = self.entry[:-1]
            elif key == 10:
                return self.entry.rstrip()
            elif key == 27:
                self.cancelled = True
                return None
            elif chr(key).isprintable():
                self.entry += chr(key)

class Base64Prompt(Prompt):
    def __init__(self, message: str, n_bytes: int | None = None):
        super().__init__(message)
        self.message = message
        if n_bytes is not None and n_bytes <= 0:
            raise ValueError('Required bytes length must be positive.')
        self.n_bytes = n_bytes

    def run(self, stdscr: curses.window) -> bytes | None:
        input_prompt = InputPrompt(self.message)
        while True:
            input = input_prompt.run(stdscr)
            if input is None:
                return None
            try:
                input_prompt.errors = self.errors
                raw_bytes = urlsafe_b64decode(input)
                if self.n_bytes is None or len(raw_bytes) == self.n_bytes:
                    return raw_bytes
                else:
                    error_message = (
                        f'Value must have an unencoded length of '
                        f'{self.n_bytes} bytes.'
                    )
                    input_prompt.errors.append(error_message)
            except binascii.Error:
                input_prompt.errors.append('Value must be valid Base64.')

class HexadecimalPrompt(Prompt):
    def __init__(self, message: str, n_bytes: int | None = None):
        super().__init__(message)
        self.input_prompt = InputPrompt(message)
        if n_bytes is not None and n_bytes <= 0:
            raise ValueError('Required bytes length must be positive.')
        self.n_bytes = n_bytes

    def run(self, stdscr: curses.window) -> bytes | None:
        while True:
            input = self.input_prompt.run(stdscr)
            if input is None:
                return None
            try:
                raw_bytes = bytes.fromhex(input)
                if self.n_bytes is None or len(raw_bytes) == self.n_bytes:
                    return raw_bytes
                else:
                    error_message = (
                        f'Value must have an unencoded length of '
                        f'{self.n_bytes} bytes.'
                    )
                    self.input_prompt.errors = [error_message]
            except ValueError:
                self.input_prompt.errors = ['Value must be valid hexadecimal.']