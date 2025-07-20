from dataclasses import dataclass
from enum import auto, Enum

type _LayoutElement = tuple[int | float, 'LayoutUnit']

class LayoutUnit(Enum):
    CHARS = auto()
    PERCENTAGE = auto()


class LayoutMeasure:
    def __init__(
            self,
            *elements: _LayoutElement,
        ) -> None:
        self.elements = list(elements)

    def calc(self, parent_chars: int):
        result = 0
        for value, unit in self.elements:
            match (unit):
                case LayoutUnit.CHARS:
                    result += int(value)
                case LayoutUnit.PERCENTAGE:
                    result += int(parent_chars * float(value) / 100.0)
        return result


@dataclass
class Layout:
    height: LayoutMeasure
    width: LayoutMeasure
    top: LayoutMeasure
    left: LayoutMeasure


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
