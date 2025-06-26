import abc
import curses
import math

class ComponentWindow(metaclass=abc.ABCMeta):
    def __init__(
            self,
            stdscr: curses.window,
            height: float,
            width: float,
            top: float,
            left: float,
            focusable: bool = True,
        ):
        self._stdscr = stdscr
        self._height = height
        self._width = width
        self._top = top
        self._left = left
        self._focusable = focusable
        self.reset_window()

    @abc.abstractmethod
    def draw(self, focused: bool):
        """
        Draw the window on the stdscr terminal.

        This function should begin by calling self._window.erase unless it
        is certain nothing will need to be erased. It should always call
        self._draw_border, and should always end with a refresh.
        """

    @abc.abstractmethod
    def handle_key(self, key: int):
        """Handle key presses when this window is focused."""

    @property
    def is_focusable(self):
        return self._focusable

    def reset_window(self):
        screen_height, screen_width = self._stdscr.getmaxyx()
        self._window = curses.newwin(
            math.floor(self._height * screen_height),
            math.floor(self._width * screen_width),
            math.floor(self._top * screen_height),
            math.floor(self._left * screen_width),
        )

    def set_focused(self, focused: bool):
        """Set whether the window is focused."""
        self._focused = focused