import abc
import curses

from enum import auto, Enum

class LayoutUnit(Enum):
    CHARS = auto()
    PERCENTAGE = auto()


type _LayoutElement = tuple[int | float, LayoutUnit]


class LayoutMeasure:
    def __init__(
            self,
            elements: _LayoutElement | list[_LayoutElement] | None = None,
        ) -> None:
        if elements is None:
            elements = []
        elif not isinstance(elements, list):
            elements = [elements]
        self.elements = elements

    def calc(self, parent_chars: int):
        result = 0
        for value, unit in self.elements:
            match (unit):
                case LayoutUnit.CHARS:
                    result += int(value)
                case LayoutUnit.PERCENTAGE:
                    result += int(parent_chars * float(value) / 100.0)
        return result


class Padding:
    def __init__(self, *args: int)-> None:
        match len(args):
            case 0:
                values = (0,) * 4
            case 1:
                values = (args[0],) * 4
            case 2:
                values = (args[0],) * 2 + (args[1],) * 2
            case 3:
                values = (args[0], args[2],) + (args[1],) * 2
            case _:
                values = args[:4]
        self.top, self.bottom, self.left, self.right = values
    
    @property
    def vertical_sum(self) -> int:
        return self.top + self.bottom
    
    @property
    def horizontal_sum(self) -> int:
        return self.left + self.right


type _PaddingType = tuple[LayoutMeasure, LayoutMeasure, LayoutMeasure, LayoutMeasure]


class ManagedWindow(metaclass=abc.ABCMeta):
    def __init__(
            self,
            height: LayoutMeasure,
            width: LayoutMeasure,
            top: LayoutMeasure,
            left: LayoutMeasure,
            padding: Padding = Padding(),
            title: str | None = None,
            bordered: bool = True,
            focusable: bool = True,
    ) -> None:
        self.height = height
        self.width = width
        self.top = top
        self.left = left
        self.padding = padding
        self.title = title
        self.bordered = bordered
        self.focusable = focusable
        self.draw_required = False
        self.window = curses.newwin(0, 0, 0, 0)
            
    @abc.abstractmethod
    def draw(self, focused: bool):
        """
        Draw the window on the stdscr terminal.

        This function should begin by calling self._window.erase unless it
        is certain nothing will need to be erased. It should usually call
        self._draw_border, and should always end with a refresh.
        """

    @abc.abstractmethod
    def handle_key(self, key: int):
        """
        Handle key presses when this instance is focused.

        When an object of this class is managed through a WindowManager
        instance and the current focus of that instance, keys not specifically
        reserved for the manager will be passed through to this method.        
        """

    def place(self, stdscr: curses.window):
        """
        Resizes and places the window within the terminal.

        This function calculates the desired size and position of the window,
        then places it on the terminal accordingly before signalling that it
        requires a fresh draw. If the window's top or left edge would fall
        outside the terminal, it will not be displayed at all. If the bottom
        or right edge would fall outside the terminal, the window will have its
        height and width reduced to fit the terminal given the top and left
        edge positioning.
        """
        parent_height, parent_width = stdscr.getmaxyx()
        top = min(self.top.calc(parent_height), parent_height)
        left = min(self.left.calc(parent_width), parent_height)
        height = min(self.height.calc(parent_height), parent_height - top)
        width = min(self.width.calc(parent_width), parent_width - left)
        if top < 0 or left < 0 or height <= 0 or width <= 0:
            self.window = curses.newwin(0, 0, 0, 0)
        else:
            self.window = curses.newwin(height, width, top, left)
        self.draw_required = True

    def _draw_border(self, focused: bool):
        if focused:
            self.window.attron(curses.A_BOLD)
        if self.bordered:
            self.window.box()
        if self.title:
            self.window.addnstr(0, 2, f' {self.title} ', len(self.title))
        self.window.attroff(curses.A_BOLD)

    def _get_internal_size(self) -> tuple[int, int]:
        height, width = self.window.getmaxyx()
        height -= self.padding.vertical_sum
        width -= self.padding.horizontal_sum
        if self.bordered:
            height -= 2
            width -= 2
        return max(0, height), max(0, width)


class WindowManager:
    def __init__(
            self,
            stdscr: curses.window,
            windows: list[ManagedWindow],
    ) -> None:
        self.stdscr = stdscr
        self.windows = windows
        self.focus_index = 0
        
    def draw_windows(self):
        for index, window in enumerate(self.windows):
            if window.draw_required:
                window.draw(index == self.focus_index)
            window.draw_required = False

    def handle_key(self, key: int):
        match key:
            case 9:
                for _ in range(len(self.windows)):
                    self.focus_index += 1
                    if self.focus_index >= len(self.windows):
                        self.focus_index = 0
                    if self.windows[self.focus_index].focusable:
                        break
            case curses.KEY_BTAB:
                for _ in range(len(self.windows)):
                    self.focus_index -= 1
                    if self.focus_index < 0:
                        self.focus_index = max(0, len(self.windows) - 1)
                    if self.windows[self.focus_index].focusable:
                        break
            case curses.KEY_RESIZE:
                self.stdscr.erase()
                for window in self.windows:
                    window.place(self.stdscr)
            case _:
                if self.windows:
                    self.windows[self.focus_index].handle_key(key)