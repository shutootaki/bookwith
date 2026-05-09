from abc import ABC, abstractmethod

from src.domain.chat.exceptions.chat_exceptions import ChatNotFoundError, ChatPermissionDeniedError
from src.domain.chat.repositories.chat_repository import ChatRepository
from src.domain.chat.value_objects.chat_id import ChatId
from src.domain.chat.value_objects.chat_title import ChatTitle
from src.domain.chat.value_objects.user_id import UserId
from src.usecase.shared.access_control import resolve_owned_or_raise


class UpdateChatTitleUseCase(ABC):
    @abstractmethod
    def execute(self, chat_id: ChatId, title: ChatTitle, user_id: UserId) -> None:
        """Chatのタイトルを更新する（所有者検証込み）"""


class UpdateChatTitleUseCaseImpl(UpdateChatTitleUseCase):
    def __init__(self, chat_repository: ChatRepository) -> None:
        self.chat_repository = chat_repository

    def execute(self, chat_id: ChatId, title: ChatTitle, user_id: UserId) -> None:
        chat = resolve_owned_or_raise(
            find_for_user=lambda: self.chat_repository.find_by_id_for_user(chat_id, user_id),
            find_any=lambda: self.chat_repository.find_by_id(chat_id),
            not_found_exc=ChatNotFoundError(f"Chat with ID {chat_id.value} not found"),
            forbidden_exc=ChatPermissionDeniedError(),
        )
        chat.assert_owned_by(user_id.value)

        chat.update_title(title)
        self.chat_repository.save(chat)
