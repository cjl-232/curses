import curses

from components.base import ComponentWindow, MeasurementUnit

class Example(ComponentWindow):

    def draw(self, focused: bool):
        self._window.erase()
        self._draw_border(focused)
        self._window.refresh()


    def handle_key(self, key: int):
        """Handle key presses when this window is active."""


    
class Body:
    def __init__(self, stdscr: curses.window):
        self.component_index = 0
        self.components: list[ComponentWindow] = [
            Example(
                stdscr=stdscr,
                height=(1.0, MeasurementUnit.PERCENTAGE),
                width=(0.2, MeasurementUnit.PERCENTAGE),
                top=(0, MeasurementUnit.PIXELS),
                left=(0, MeasurementUnit.PIXELS),
                title='Window 1',
            ),
            Example(
                stdscr=stdscr,
                height=(0.9, MeasurementUnit.PERCENTAGE),
                width=(0.8, MeasurementUnit.PERCENTAGE),
                top=(0, MeasurementUnit.PIXELS),
                left=(0.2, MeasurementUnit.PERCENTAGE),
                title='Window 2',
            ),
            Example(
                stdscr=stdscr,
                height=(0.1, MeasurementUnit.PERCENTAGE),
                width=(0.8, MeasurementUnit.PERCENTAGE),
                top=(0.9, MeasurementUnit.PERCENTAGE),
                left=(0.2, MeasurementUnit.PERCENTAGE),
                title='Window 3',
            ),
        ]

    

    def run(self, stdscr: curses.window):
        stdscr.keypad(True)
        self._draw_components()
        stdscr.refresh()
        while True:
            self._draw_components()
            key = stdscr.getch()
            if key == 81 or key == 113: # Q
                break
            elif key == 9: # TAB
                for _ in range(len(self.components)):
                    self.component_index += 1
                    if self.component_index >= len(self.components):
                        self.component_index = 0
                    if self.components[self.component_index].is_focusable:
                        break
            elif key == curses.KEY_RESIZE:
                stdscr.erase()                
                for component in self.components:
                    component.reset_window()

    def _draw_components(self):
        for index, component in enumerate(self.components):
            component.draw(index == self.component_index)

curses.wrapper(lambda stdscr: Body(stdscr).run(stdscr))