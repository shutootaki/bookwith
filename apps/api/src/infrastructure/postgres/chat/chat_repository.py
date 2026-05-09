from datetime import datetime

from sqlalchemy.orm import Session

from src.domain.chat.entities.chat import Chat
from src.domain.chat.repositories.chat_repository import ChatRepository
from src.domain.chat.value_objects.book_id import BookId
from src.domain.chat.value_objects.chat_id import ChatId
from src.domain.chat.value_objects.user_id import UserId
from src.infrastructure.postgres.chat.chat_dto import ChatDTO


class ChatRepositoryImpl(ChatRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, chat: Chat) -> None:
        try:
            # 論理削除済みのレコードも含めて検索し、ID 衝突による IntegrityError を回避する。
            existing_chat = (
                self._session.query(ChatDTO)
                .filter(ChatDTO.id == chat.id.value)
                .first()
            )

            if existing_chat:
                # B-15: 部分更新では title のみ確実に更新する。book_id は値が None でも上書きしない。
                existing_chat.title = chat.title.value
                if chat.book_id is not None:
                    existing_chat.book_id = chat.book_id.value
            else:
                chat_dto = ChatDTO.from_entity(chat)
                self._session.add(chat_dto)

            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

    def find_by_id(self, chat_id: ChatId) -> Chat | None:
        chat_dto = (
            self._session.query(ChatDTO)
            .filter(ChatDTO.id == chat_id.value, ChatDTO.deleted_at == None)
            .first()
        )
        if chat_dto is None:
            return None

        return chat_dto.to_entity()

    def find_by_id_for_user(self, chat_id: ChatId, user_id: UserId) -> Chat | None:
        # CR-3: user_id を WHERE 句に必ず含める。
        chat_dto = (
            self._session.query(ChatDTO)
            .filter(
                ChatDTO.id == chat_id.value,
                ChatDTO.user_id == user_id.value,
                ChatDTO.deleted_at == None,
            )
            .first()
        )
        if chat_dto is None:
            return None
        return chat_dto.to_entity()

    def find_by_user_id(self, user_id: UserId) -> list[Chat]:
        chat_dtos = (
            self._session.query(ChatDTO)
            .filter(ChatDTO.user_id == user_id.value, ChatDTO.deleted_at == None)
            .order_by(ChatDTO.updated_at.desc())
            .all()
        )
        return [dto.to_entity() for dto in chat_dtos]

    def find_by_book_id(self, book_id: BookId) -> list[Chat]:
        chat_dtos = (
            self._session.query(ChatDTO)
            .filter(ChatDTO.book_id == book_id.value, ChatDTO.deleted_at == None)
            .all()
        )
        return [dto.to_entity() for dto in chat_dtos]

    def find_by_user_id_and_book_id(self, user_id: UserId, book_id: BookId) -> list[Chat]:
        chat_dtos = (
            self._session.query(ChatDTO)
            .filter(
                ChatDTO.user_id == user_id.value,
                ChatDTO.book_id == book_id.value,
                ChatDTO.deleted_at == None,
            )
            .all()
        )
        return [dto.to_entity() for dto in chat_dtos]

    def delete_for_user(self, chat_id: ChatId, user_id: UserId) -> bool:
        try:
            now = datetime.now()
            result = (
                self._session.query(ChatDTO)
                .filter(
                    ChatDTO.id == chat_id.value,
                    ChatDTO.user_id == user_id.value,
                    ChatDTO.deleted_at == None,
                )
                .update({"deleted_at": now, "updated_at": now})
            )
            if result > 0:
                self._session.commit()
                return True
            return False
        except Exception:
            self._session.rollback()
            raise
