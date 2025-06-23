import abc

from curses import window
from typing import Any

class Component(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def run(self, stdscr: window) -> Any:
        """Display and run the component on the terminal."""
