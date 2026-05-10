"""メッセージ削除のユースケース"""

from abc import ABC, abstractmethod

from src.domain.message.exceptions.message_exceptions import MessageNotFoundException
from src.domain.message.repositories.message_repository import MessageRepository
from src.domain.message.value_objects.message_id import MessageId


class DeleteMessageUseCase(ABC):
    @abstractmethod
    def execute(self, message_id: str, user_id: str) -> None:
        """メッセージを削除する（所有者検証込み）"""

    @abstractmethod
    def execute_bulk(self, message_ids: list[str], user_id: str) -> list[str]:
        """複数のメッセージを一括削除する。削除に失敗したメッセージIDのリストを返す（所有者検証込み）"""


class DeleteMessageUseCaseImpl(DeleteMessageUseCase):
    def __init__(self, message_repository: MessageRepository) -> None:
        self.message_repository = message_repository

    def execute(self, message_id: str, user_id: str) -> None:
        message_id_obj = MessageId(message_id)
        if not self.message_repository.delete_for_user(message_id_obj, user_id):
            raise MessageNotFoundException(message_id)

    def execute_bulk(self, message_ids: list[str], user_id: str) -> list[str]:
        """複数のメッセージを一括削除する（所有者検証込み）。
        削除に失敗した（=所有者でない、または存在しない）IDのリストを返す.
        """
        message_id_objects = [MessageId(id_str) for id_str in message_ids]

        deleted_ids = self.message_repository.bulk_delete_for_user(message_id_objects, user_id)
        deleted_set = {mid.value for mid in deleted_ids}

        # B-5: 「削除した ID」と「失敗した ID」を正しく区別する。
        return [mid for mid in message_ids if mid not in deleted_set]
