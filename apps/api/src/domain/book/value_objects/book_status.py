import enum
from dataclasses import dataclass


class BookStatusEnum(enum.Enum):
    NOT_STARTED = "not_started"  # 未読
    IN_PROGRESS = "in_progress"  # 読書中
    COMPLETED = "completed"  # 読了


@dataclass(frozen=True)
class BookStatus:
    value: BookStatusEnum

    def __post_init__(self):
        if not isinstance(self.value, BookStatusEnum):
            raise ValueError("無効なステータス値です")

    def is_not_started(self) -> bool:
        """未読かどうかを返します。"""
        return self.value == BookStatusEnum.NOT_STARTED

    def is_in_progress(self) -> bool:
        """読書中かどうかを返します。"""
        return self.value == BookStatusEnum.IN_PROGRESS

    def is_completed(self) -> bool:
        """読了かどうかを返します。"""
        return self.value == BookStatusEnum.COMPLETED
