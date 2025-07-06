from enum import auto, Enum

class State(Enum):
    STANDARD = auto()
    NEXT_WINDOW = auto()
    PREV_WINDOW = auto()
    RESIZE = auto()
    ADD_CONTACT = auto()
    TERMINATE = auto()