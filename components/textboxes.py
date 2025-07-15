from enum import auto, Enum

from states import State
from styling import Layout, Padding
from windows import ManagedWindow

class Alignment(Enum):
    LEFT = auto()
    RIGHT = auto()

class Textbox(ManagedWindow):
    def __init__(
            self,
            text_lines: list[str],
            layout: Layout,
            padding: Padding | None = None,
            title: str | None = None,
            footer: str | None = None,
            bordered: bool = False,
            alignment: Alignment = Alignment.LEFT,
            attributes: list[int] | None = None
    ) -> None:
        super().__init__(layout, padding, title, footer, bordered, False)
        self.text_lines = text_lines
        self.alignment = alignment
        self.attributes = attributes or []

    def handle_key(self, key: int) -> State:
        return State.STANDARD

    def draw(self, focused: bool):
        self.window.erase()
        height, width = self._get_internal_size()
        if height <= 0 or width <= 0:
            self.window.refresh()
            return
        self._draw_external(focused)
        top, left = self._get_top_left()
        for attribute in self.attributes:
            self.window.attron(attribute)
        for index, text in enumerate(self.text_lines[:height]):
            match self.alignment:
                case Alignment.LEFT:
                    visible_text = text[:width]
                case Alignment.RIGHT:
                    visible_text = text[-width:]
                    if width > len(visible_text):
                        padding = ' ' * (width - len(visible_text))
                        visible_text = padding + visible_text
            self.window.addnstr(top + index, left, visible_text, width)
        for attribute in self.attributes:
            self.window.attroff(attribute)
        self.window.refresh()
        self.draw_required = False