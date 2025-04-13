from dataclasses import dataclass


@dataclass(frozen=True)
class AnnotationCfi:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("CFI is required")
        if not isinstance(self.value, str):
            raise ValueError("CFI must be a string")

    @classmethod
    def from_string(cls, cfi_str: str) -> "AnnotationCfi":
        return cls(cfi_str)
