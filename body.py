# Need to work out combinations (100% - 200px)

import curses

from components.base import ComponentWindow, MeasurementUnit
from components.contacts import ContactsMenu
from components.logs import Log
from components.messages import MessageEntry, MessageLog

class Example(ComponentWindow):

    def draw(self, focused: bool):
        self._window.erase()
        self._draw_border(focused)
        self._window.refresh()
        self.draw_required = False


    def handle_key(self, key: int):
        """Handle key presses when this window is active."""



from sqlalchemy import create_engine
from database.models import Base, Contact
engine = create_engine('sqlite:///contacttest.db')
Base.metadata.create_all(engine)
from sqlalchemy.orm import Session
from database.schemas.outputs import ContactOutputSchema
# with Session(engine) as session:
#     for _ in range(20):
#         contact = Contact(name=f'Contact #{token_hex(8)}', verification_key=urlsafe_b64encode(token_bytes(32)).decode())
#         session.add(contact)
#     session.commit()

refreshes = {0: 0, 1: 0, 2: 0, 3: 0}

class Body:
    def __init__(self, stdscr: curses.window):
        with Session(engine) as session:
            contact = ContactOutputSchema.model_validate(session.get(Contact, 1))
        self.component_index = 0
        output_log = Log(
            stdscr=stdscr,
            height=(0.2, MeasurementUnit.PERCENTAGE),
            width=(1.0, MeasurementUnit.PERCENTAGE),
            top=(0.8, MeasurementUnit.PERCENTAGE),
            left=(0, MeasurementUnit.PIXELS),
            title='Output',
        )
        message_entry = MessageEntry(
            engine=engine,
            contact=contact,
            output_log=output_log,
            stdscr=stdscr,
            height=(0.2, MeasurementUnit.PERCENTAGE),
            width=(0.8, MeasurementUnit.PERCENTAGE),
            top=(0.6, MeasurementUnit.PERCENTAGE),
            left=(0.2, MeasurementUnit.PERCENTAGE),
        )
        message_log = MessageLog(
            engine=engine,
            contact=contact,
            output_log=output_log,
            stdscr=stdscr,
            height=(0.6, MeasurementUnit.PERCENTAGE),
            width=(0.8, MeasurementUnit.PERCENTAGE),
            top=(0.0, MeasurementUnit.PERCENTAGE),
            left=(0.2, MeasurementUnit.PERCENTAGE),
        )
        self.components: list[ComponentWindow] = [
            ContactsMenu(
                engine=engine,
                message_entry=message_entry,
                message_log=message_log,
                stdscr=stdscr,
                height=(0.8, MeasurementUnit.PERCENTAGE),
                width=(0.2, MeasurementUnit.PERCENTAGE),
                top=(0, MeasurementUnit.PIXELS),
                left=(0, MeasurementUnit.PIXELS),
                title='Contacts',
            ),
            message_log,
            message_entry,
            output_log,
        ]

    def run(self, stdscr: curses.window):
        stdscr.keypad(True)
        stdscr.nodelay(True)
        stdscr.clear()
        stdscr.refresh()
        for component in self.components:
            component.reset_window()
        while True:
            self._draw_components()
            active_component = self.components[self.component_index]
            key = stdscr.getch()
            if key == 81 or key == 113: # Q
                if not isinstance(active_component, MessageEntry):
                    break
                else:
                    active_component.handle_key(key)
            elif key == 9 or key == curses.KEY_BTAB: # TAB or SHIFT-TAB
                self.components[self.component_index].draw_required = True
                for _ in range(len(self.components)):
                    if key == 9:
                        self.component_index += 1
                        if self.component_index >= len(self.components):
                            self.component_index = 0
                    else:
                        self.component_index -= 1
                        if self.component_index < 0:
                            self.component_index = len(self.components) - 1
                    if self.components[self.component_index].is_focusable:
                        break
                self.components[self.component_index].draw_required = True
            elif key == curses.KEY_RESIZE:
                stdscr.erase()                
                for component in self.components:
                    component.reset_window()
                stdscr.refresh()
            else:
                self.components[self.component_index].handle_key(key)

    def _draw_components(self):
        for index, component in enumerate(self.components):
            if component.draw_required:
                refreshes[index] += 1
                component.draw(index == self.component_index)

curses.wrapper(lambda stdscr: Body(stdscr).run(stdscr))
print(refreshes)