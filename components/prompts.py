import abc
import curses

from enum import auto, Enum
from typing import Any

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
            



        match key:
            case 8 | curses.KEY_BACKSPACE:
                node.input = node.input[:-1]
                self.draw_required = True
            case 10 | curses.KEY_ENTER:
                self.node_index += 1
                if self.node_index >= len(self.nodes):
                    return State.PROMPT_SUBMITTED
                else:
                    self.draw_required = True
            case 27:  # Esc
                node.input = ''
                self.node_index -= 1
                if self.node_index < 0:
                    return State.PROMPT_CANCELLED
                else:
                    self.draw_required = True
            case _:
                if 0 <= key <= 0x10ffff and chr(key).isascii():
                    node.input += chr(key)
                    self.draw_required = True
        return State.PROMPT_ACTIVE
    
    def run(self) -> dict[str, Any] | None:
        state = _PromptState.STANDARD
        while True:
            node = self.nodes[self.node_index]




# # TODO SCRAP THIS REPLACE WITH CUSTOM TYPE, NOT LOG. BOTTOM UP IS NOT HELPFUL

# import abc
# import curses

# from enum import StrEnum
# from typing import Any

# from components.base import MeasurementUnit
# from components.logs import Log

# class Prompt(Log, metaclass=abc.ABCMeta):
#     def __init__(
#             self,
#             stdscr: curses.window,
#             message: str,
#             title: str | None = None,
#         ):
#         super().__init__(
#             stdscr=stdscr,
#             height=(1.0, MeasurementUnit.PERCENTAGE),
#             width=(1.0, MeasurementUnit.PERCENTAGE),
#             top=(0, MeasurementUnit.PIXELS),
#             left=(0, MeasurementUnit.PIXELS),
#             bordered=False,
#             title=title,
#         )
#         self._message = message
#         self._errors: list[str] = list()

#     @abc.abstractmethod
#     def run(self) -> Any:
#         pass


# class ChoicePrompt(Prompt):
#     def __init__(
#             self,
#             stdscr: curses.window,
#             message: str,
#             choices: type[StrEnum],
#             title: str | None = None,
#         ):
#         super().__init__(stdscr, message, title)
#         if len(choices) == 0:
#             raise ValueError('At least one choice is required per prompt.')
#         elif len(choices) > 9:
#             raise ValueError('No more than 9 choices are allowed per prompt.')
#         self.add_item(message, False, title)
#         for index, choice in enumerate(choices):
#             self.add_item(f'{index}. {choice.value}', False)
#         self._choices = [x.value for x in choices]
#         print(self._item_lines)

#     def run(self) -> str | None:
#         curses.curs_set(0)
#         self._stdscr.keypad(True)
#         self._stdscr.nodelay(False)
#         self.reset_window()
#         while True:
#             if self.draw_required:
#                 self.draw(True)
#             key = self._window.getch()
#             if 49 <= key < 49 + len(self._choices):
#                 return self._choices[int(chr(key)) - 1]
#             elif key == 27:
#                 return None
#             elif key == curses.KEY_RESIZE:
#                 self.reset_window()
#             else:
#                 super().handle_key(key)
    
#     def reset_window(self):
#         super().reset_window()
#         height = self._get_internal_size()[0]
#         self._scroll_index = max(0, height - len(self._item_lines))
        
# class SignatureKeyMethodPrompt(ChoicePrompt):
#     def __init__(self, stdscr: curses.window):
#         super().__init__(stdscr, 'Message here', self.Choices, 'Title here')

#     class Choices(StrEnum):
#         BASE64 = 'Base64 Input'
#         HEXADECIMAL = 'Hexadecimal Input'
#         FROM_PEM_FILE = 'From PEM-encoded File'
# # class InputPrompt(Prompt):
# #     def __init__(self, message: str, max_length: int | None = None):
# #         super().__init__(message)
# #         self.entry = ''
# #         self.message = message
# #         if max_length is not None and max_length < 1:
# #             raise ValueError('Max length must be positive.')
# #         self.max_length = max_length

# #     def run(self, stdscr: curses.window) -> str | None:
# #         curses.curs_set(1)
# #         while True:
# #             stdscr.clear()
# #             stdscr.nodelay(settings.display.await_inputs == False)
# #             height = stdscr.getmaxyx()[0]
# #             y_pos = height - 1
# #             stdscr.move(y_pos, len(self.entry))
# #             stdscr.addstr(y_pos, 0, self.entry)
# #             for error in self.errors[::-1]:
# #                 y_pos -= 1
# #                 stdscr.addstr(y_pos, 0, error)
# #             y_pos -= 1
# #             stdscr.addstr(y_pos, 0, self.message)
# #             stdscr.move(height - 1, len(self.entry))
# #             stdscr.refresh()
# #             key = stdscr.getch()
# #             match key:
# #                 case -1:
# #                     pass
# #                 case 8 | curses.KEY_BACKSPACE:
# #                     self.entry = self.entry[:-1]
# #                 case 10:
# #                     return self.entry.rstrip()
# #                 case 27:
# #                     return None
# #                 case _:
# #                     if chr(key).isprintable():
# #                         self.entry += chr(key)
# #             if self.max_length is not None:
# #                 self.entry = self.entry[:self.max_length]

# # class Base64Prompt(Prompt):
# #     def __init__(
# #             self,
# #             message: str,
# #             max_length: int,
# #             n_bytes: int | None = None,
# #         ):
# #         super().__init__(message)
# #         self.input_prompt = InputPrompt(message, max_length)
# #         if n_bytes is not None and n_bytes <= 0:
# #             raise ValueError('Required bytes length must be positive.')
# #         self.n_bytes = n_bytes

# #     def run(self, stdscr: curses.window) -> bytes | None:
# #         while True:
# #             input = self.input_prompt.run(stdscr)
# #             if input is None:
# #                 return None
# #             try:
# #                 self.input_prompt.errors = self.errors
# #                 raw_bytes = urlsafe_b64decode(input)
# #                 if self.n_bytes is None or len(raw_bytes) == self.n_bytes:
# #                     return raw_bytes
# #                 else:
# #                     error_message = (
# #                         f'Value must have an unencoded length of '
# #                         f'{self.n_bytes} bytes.'
# #                     )
# #                     self.input_prompt.errors.append(error_message)
# #             except binascii.Error:
# #                 self.input_prompt.errors.append('Value must be valid Base64.')

# # class HexadecimalPrompt(Prompt):
# #     def __init__(
# #             self,
# #             message: str,
# #             max_length: int,
# #             n_bytes: int | None = None,
# #         ):
# #         super().__init__(message)
# #         self.input_prompt = InputPrompt(message, max_length)
# #         if n_bytes is not None and n_bytes <= 0:
# #             raise ValueError('Required bytes length must be positive.')
# #         self.n_bytes = n_bytes

# #     def run(self, stdscr: curses.window) -> bytes | None:
# #         while True:
# #             input = self.input_prompt.run(stdscr)
# #             if input is None:
# #                 return None
# #             try:
# #                 raw_bytes = bytes.fromhex(input)
# #                 if self.n_bytes is None or len(raw_bytes) == self.n_bytes:
# #                     return raw_bytes
# #                 else:
# #                     error_message = (
# #                         f'Value must have an unencoded length of '
# #                         f'{self.n_bytes} bytes.'
# #                     )
# #                     self.input_prompt.errors = [error_message]
# #             except ValueError:
# #                 self.input_prompt.errors = ['Value must be valid hexadecimal.']