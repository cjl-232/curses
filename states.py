from enum import auto, Enum

class State(Enum):
    STANDARD = auto()
    NEXT_WINDOW = auto()
    PREV_WINDOW = auto()
    RESIZE = auto()
    PROMPT_ACTIVE = auto()
    PROMPT_SUBMITTED = auto()
    PROMPT_CANCELLED = auto()
    ADD_CONTACT = auto()
    SELECT_CONTACT = auto()
    SEND_MESSAGE = auto()
    TERMINATE = auto()