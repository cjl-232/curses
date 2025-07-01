import abc
import curses
import enum
import math

from settings import settings

class Direction(enum.Enum):
    VERTICAL = 1
    HORIZONTAL = 2

class MeasurementUnit(enum.Enum):
    PIXELS = 1
    PERCENTAGE = 2

type Measurement = tuple[int | float, MeasurementUnit]

class ComponentWindow(metaclass=abc.ABCMeta):
    def __init__(
            self,
            stdscr: curses.window,
            height: Measurement,
            width: Measurement,
            top: Measurement,
            left: Measurement,
            title: str | None = None,
            bordered: bool = True,
            focusable: bool = True,
        ):
        self._stdscr = stdscr
        self._height = height
        self._width = width
        self._top = top
        self._left = left
        self._title = title
        self._focusable = focusable
        self._window = curses.newwin(0, 0)
        self.draw_required: bool = True
        self._bordered = bordered

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
        self._window = curses.newwin(
            self._calculate_size(self._height, Direction.VERTICAL),
            self._calculate_size(self._width, Direction.HORIZONTAL),
            self._calculate_size(self._top, Direction.VERTICAL),
            self._calculate_size(self._left, Direction.HORIZONTAL),
        )
        self.draw_required = True

    def _calculate_size(self, size: Measurement, direction: Direction) -> int:
        value, unit = size
        match unit:
            case MeasurementUnit.PIXELS:
                return int(value)
            case MeasurementUnit.PERCENTAGE:
                screen_height, screen_width = self._stdscr.getmaxyx()
                match direction:
                    case Direction.VERTICAL:
                        return math.floor(value * screen_height)
                    case Direction.HORIZONTAL:
                        return math.floor(value * screen_width)
                    
    def _draw_border(self, focused: bool):
        if focused:
            self._window.attron(curses.A_BOLD)
        if self._bordered:
            self._window.box()
        if self._title:
            self._window.addstr(0, 2, f' {self._title} ')
        self._window.attroff(curses.A_BOLD)

    def _get_internal_size(self) -> tuple[int, int]:
        display = settings.display
        height, width = self._window.getmaxyx()
        height -= display.top_padding + display.bottom_padding
        width -= display.left_padding + display.right_padding
        if self._bordered:
            height -= 2
            width -= 2
        return height, width