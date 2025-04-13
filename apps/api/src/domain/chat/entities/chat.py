from datetime import datetime

from src.domain.chat.value_objects.book_id import BookId
from src.domain.chat.value_objects.chat_id import ChatId
from src.domain.chat.value_objects.chat_title import ChatTitle
from src.domain.chat.value_objects.user_id import UserId


class Chat:
    def __init__(
        self,
        id: ChatId,
        user_id: UserId,
        title: ChatTitle | None = None,
        book_id: BookId | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        self._id = id
        self._user_id = user_id
        self._title = title
        self._book_id = book_id
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @property
    def id(self) -> ChatId:
        return self._id

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def title(self) -> ChatTitle | None:
        return self._title

    @property
    def book_id(self) -> BookId | None:
        return self._book_id

    @property
    def created_at(self) -> datetime | None:
        return self._created_at

    @property
    def updated_at(self) -> datetime | None:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    def __eq__(self, obj: object) -> bool:
        if isinstance(obj, Chat):
            return self._id == obj._id
        return False

    def update_title(self, title: ChatTitle) -> None:
        self._title = title
        self._updated_at = datetime.now()

    def update_book_id(self, book_id: BookId | None) -> None:
        self._book_id = book_id
        self._updated_at = datetime.now()

    @classmethod
    def create(cls, user_id: UserId, title: ChatTitle | None = None, book_id: BookId | None = None) -> "Chat":
        from uuid import uuid4

        return cls(
            id=ChatId(value=str(uuid4())),
            user_id=user_id,
            title=title,
            book_id=book_id,
        )
