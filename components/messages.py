import curses
import textwrap

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from components.base import ComponentWindow, Measurement
from database.models import Message, MessageType
from database.outputs.schemas import ContactOutputSchema, MessageOutputSchema
from settings import settings

class MessageLog(ComponentWindow):
    def __init__(
            self,
            engine: Engine,
            contact: ContactOutputSchema | None,
            stdscr: curses.window,
            height: Measurement,
            width: Measurement,
            top: Measurement,
            left: Measurement,
            focusable: bool = True,
        ):
        self._engine = engine
        self._contact = contact
        self._scroll_index: int = 0 # Scroll upwards
        self._message_lines: list[tuple[str, bool]] = list()
        self._loaded_nonces: list[str] = list()
        super().__init__(
            stdscr=stdscr,
            height=height,
            width=width,
            top=top,
            left=left,
            title=contact.name if contact is not None else None,
            focusable=focusable,
        )

    def draw(self, focused: bool):
        self._window.erase()
        self._draw_border(focused)
        height, width = (x - 2 for x in self._window.getmaxyx())
        if height <= 0 or width <= 0:
            self._window.refresh()
            self.draw_required = False
            return
        if self._scroll_index == 0:
            visible_lines = self._message_lines[-height:]
        else:
            start = 0 - height - self._scroll_index
            stop = -self._scroll_index
            visible_lines = self._message_lines[start:stop]
        for index, (line, header) in enumerate(visible_lines):
            if header:
                self._window.attron(curses.A_BOLD)
                self._window.addnstr(index + 1, 1, line, width)
                self._window.attroff(curses.A_BOLD)
            else:
                self._window.addnstr(index + 1, 1, line, width)
        self._window.refresh()
        self.draw_required = False

    def handle_key(self, key: int):
        height = self._window.getmaxyx()[0] - 2
        if key in settings.key_bindings.up_key_set:
            self._scroll_index += 1
            if self._scroll_index >= len(self._message_lines) - height:
                self._scroll_index = len(self._message_lines) - 1 - height
            self.draw_required = True
        elif key in settings.key_bindings.down_key_set:
            self._scroll_index -= 1
            if self._scroll_index < 0:
                self._scroll_index = 0
            self.draw_required = True
        elif key == curses.KEY_F5:
            self.update()
        elif key == 281: # SHIFT-F5
            self._refresh()

    def reset_window(self):
        super().reset_window()
        self._refresh()

    def set_contact(self, contact: ContactOutputSchema | None):
        if self._contact is None and contact is None:
            return
        elif self._contact is not None and contact is not None:
            if self._contact.id == contact.id:
                return
        self._contact = contact
        if contact is not None:
            self.title = contact.name
        else:
            self.title = None
        self._refresh()
        self.draw_required = True

    def update(self):
        self._load_messages()

    def _format_message(
            self,
            message: MessageOutputSchema
        ) -> list[tuple[str, bool]]:
        width = self._window.getmaxyx()[1] - 2
        if width <= 0:
            return []
        wrapped_text = textwrap.wrap(message.text, width)
        if wrapped_text:
            assert self._contact is not None
            if message.message_type == MessageType.received:
                name = f'{self._contact.name}:'
            else:
                name = 'You:'
            header = (
                f'{name: <{max(0, width - 16)}}'
                f'{message.timestamp.strftime('%Y-%m-%d %H:%M')}'
            )
            result = [('', False), (header[:width], True)]
            for line in wrapped_text:
                result.append((line, False))
            return result
        return []

    def _load_messages(self):
        if self._contact is None:
            return
        width = self._window.getmaxyx()[1] - 2
        if width <= 0:
            return
        with Session(self._engine) as session:
            query = (
                select(Message)
                .where(Message.contact_id == self._contact.id)
                .where(~Message.nonce.in_(self._loaded_nonces))
                .order_by(Message.timestamp)
            )
            for obj in session.scalars(query):
                output = MessageOutputSchema.model_validate(obj)
                for line in self._format_message(output):
                    if self._scroll_index > 0:
                        self._scroll_index += 1
                    self._message_lines.append(line)
                self._loaded_nonces.append(output.nonce)
                self.draw_required = True

    def _refresh(self):
        self._loaded_nonces.clear()
        self._message_lines.clear()
        self._scroll_index = 0
        self._load_messages()
