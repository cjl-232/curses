import abc

from curses import window

class Component(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def run(self, stdscr: window):
        """Display and run the component on the terminal."""
