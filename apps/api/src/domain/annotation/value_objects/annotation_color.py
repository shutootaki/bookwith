from dataclasses import dataclass
from enum import Enum


class AnnotationColorEnum(Enum):
    YELLOW = "yellow"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


@dataclass(frozen=True)
class AnnotationColor:
    value: str | None

    def __post_init__(self) -> None:
        if self.value is not None and not any(self.value == color.value for color in AnnotationColorEnum):
            raise ValueError(f"Invalid annotation color: {self.value}")

    @classmethod
    def yellow(cls) -> "AnnotationColor":
        return cls(AnnotationColorEnum.YELLOW.value)

    @classmethod
    def red(cls) -> "AnnotationColor":
        return cls(AnnotationColorEnum.RED.value)

    @classmethod
    def green(cls) -> "AnnotationColor":
        return cls(AnnotationColorEnum.GREEN.value)

    @classmethod
    def blue(cls) -> "AnnotationColor":
        return cls(AnnotationColorEnum.BLUE.value)

    @classmethod
    def from_string(cls, color_str: str | None) -> "AnnotationColor":
        return cls(color_str)
