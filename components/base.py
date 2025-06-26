import abc
import curses

class ComponentWindow(metaclass=abc.ABCMeta):
    def __init__(
            self,
            height: int,
            width: int,
            top: int = 0,
            left: int = 0,
            bordered: bool = True,
            focusable: bool = True
        ):
        self._window = curses.newwin(height, width, top, left)
        self._bordered = bordered
        self._focused = False
        self._focusable = focusable

    @abc.abstractmethod
    def draw(self):
        """
        Draw the window on the stdscr terminal.

        This function should begin by calling self._window.erase, unless it
        is certain nothing will need to be erased. It should always draw a
        border if self._bordered == True. It should always conclude by calling
        self._window.refresh.
        """

    @abc.abstractmethod
    def handle_key(self, key: int):
        """Handle key presses when this window is active."""

    @property
    def is_focusable(self):
        return self._focusable

    def resize(self, height: int, width: int, top: int = 0, left: int = 0):
        self._window = curses.newwin(height, width, top, left)

    def set_focused(self, focused: bool):
        """Set whether the window is focused. Redraw borders if relevant."""
        if focused != self._focused and self._bordered:
            if focused:
                self._window.attron(curses.A_BOLD)
                self._window.box()
                self._window.attroff(curses.A_BOLD)
            else:
                self._window.box()
        self._focused = focused