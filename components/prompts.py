import abc
import curses

from enum import auto, Enum

from states import State
from styling import Layout, LayoutMeasure, LayoutUnit, Padding
from windows import ManagedWindow

_fullscreen_layout = Layout(
    height=LayoutMeasure((100, LayoutUnit.PERCENTAGE)),
    width=LayoutMeasure((100, LayoutUnit.PERCENTAGE)),
    top=LayoutMeasure((0, LayoutUnit.CHARS)),
    left=LayoutMeasure((0, LayoutUnit.CHARS)),
)

class _PromptState(Enum):
    STANDARD = auto()
    CHANGED = auto()
    SUBMITTED = auto()
    CANCELLED = auto()


class _PromptNode(metaclass=abc.ABCMeta):
    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message

    @abc.abstractmethod
    def get_lines(self) -> list[str]:
        pass

    @abc.abstractmethod
    def handle_key(self, key: int) -> _PromptState:
        pass


class ChoicePromptNode[T: Enum](_PromptNode):
    def __init__(self, name: str, message: str, choice: T, *choices: T):
        super().__init__(name, message)
        self.choices = [choice] + list(choices)
        if len(self.choices) > 9:
            raise ValueError('No more than 9 choices allowed per node.')
        self.input: T

    def get_lines(self) -> list[str]:
        result = [self.message]
        for index, choice in enumerate(self.choices):
            result.append(f'{index + 1}. {choice.value}')
        result.append('')
        return result

    def handle_key(self, key: int) -> _PromptState:
        match key:
            case 27:  # Esc
                return _PromptState.CANCELLED
            case _:
                if 49 <= key < 49 + len(self.choices):
                    self.input = self.choices[key - 49]
                    return _PromptState.SUBMITTED
        return _PromptState.STANDARD


class TextPromptNode(_PromptNode):
    def __init__(self, name: str, message: str):
        super().__init__(name, message)
        self.input = ''

    def get_lines(self) -> list[str]:
        return [self.message, self.input]

    def handle_key(self, key: int) -> _PromptState:
        match key:
            case 8 | curses.KEY_BACKSPACE:
                if self.input:
                    self.input = self.input[:-1]
                    return _PromptState.CHANGED
            case 10 | curses.KEY_ENTER:
                return _PromptState.SUBMITTED
            case 27:  # Esc
                return _PromptState.CANCELLED
            case _:
                if 0 <= key <= 0x10ffff and chr(key).isascii():
                    self.input += chr(key)
                    return _PromptState.CHANGED
        return _PromptState.STANDARD
    

class Prompt(ManagedWindow):
    def __init__(self, node: _PromptNode, *nodes: _PromptNode) -> None:
        super().__init__(_fullscreen_layout, Padding(0, 1), bordered=False)
        self.nodes = [node] + list(nodes)
        self.node_index = 0

    def draw(self, focused: bool = True):
        self.window.erase()

        # Determine the current node and lines.
        node = self.nodes[self.node_index]
        lines = node.get_lines()

        # Set cursor visibility.
        if isinstance(node, ChoicePromptNode):
            curses.curs_set(0)
        elif isinstance(node, TextPromptNode):
            curses.curs_set(1 if focused else 0)

        # Determine the space available for input, and halt if insufficient.
        height, width = self._get_internal_size()
        if height <= len(lines) or width <= 0:
            self.window.refresh()
            self.draw_required = False
            return

        # Draw the prompt text and input to the screen.
        y_pos = self.padding.top + height - len(lines)
        x_pos = self.padding.left
        for index, line in enumerate(lines):
            self.window.addnstr(y_pos + index, x_pos, line, width)
        if isinstance(node, TextPromptNode):
            self.window.addch(y_pos + len(lines) - 1, width - 1, ' ')
            self.window.move(y_pos + len(lines) - 1, width - 1)
        
        # Refresh the window.
        self.window.refresh()
        self.draw_required = False
    
    def handle_key(self, key: int) -> State:
        match self.nodes[self.node_index].handle_key(key):
            case _PromptState.STANDARD:
                pass
            case _PromptState.CHANGED:
                self.draw_required = True
            case _PromptState.SUBMITTED:
                self.node_index += 1
                if self.node_index >= len(self.nodes):
                    return State.PROMPT_SUBMITTED
                else:
                    self.draw_required = True
            case _PromptState.CANCELLED:
                self.node_index -= 1
                if self.node_index < 0:
                    return State.PROMPT_CANCELLED
                else:
                    self.draw_required = True
        return State.PROMPT_ACTIVE