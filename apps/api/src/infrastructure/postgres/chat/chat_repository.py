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
            existing_chat = self._session.query(ChatDTO).filter(ChatDTO.id == chat.id.value).first()

            if existing_chat:
                existing_chat.title = chat.title.value
                existing_chat.book_id = chat.book_id.value if chat.book_id else None
            else:
                chat_dto = ChatDTO.from_entity(chat)
                self._session.add(chat_dto)

            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e

    def find_by_id(self, chat_id: ChatId) -> Chat | None:
        chat_dto = self._session.query(ChatDTO).filter(ChatDTO.id == chat_id.value).first()
        if chat_dto is None:
            return None

        return chat_dto.to_entity()

    def find_by_user_id(self, user_id: UserId) -> list[Chat]:
        chat_dtos = self._session.query(ChatDTO).filter(ChatDTO.user_id == user_id.value).order_by(ChatDTO.updated_at.desc()).all()
        return [dto.to_entity() for dto in chat_dtos]

    def find_by_book_id(self, book_id: BookId) -> list[Chat]:
        chat_dtos = self._session.query(ChatDTO).filter(ChatDTO.book_id == book_id.value).all()
        return [dto.to_entity() for dto in chat_dtos]

    def find_by_user_id_and_book_id(self, user_id: UserId, book_id: BookId) -> list[Chat]:
        chat_dtos = self._session.query(ChatDTO).filter(ChatDTO.user_id == user_id.value, ChatDTO.book_id == book_id.value).all()
        return [dto.to_entity() for dto in chat_dtos]

    def delete(self, chat_id: ChatId) -> None:
        try:
            chat_dto = self._session.query(ChatDTO).filter(ChatDTO.id == chat_id.value).first()
            if chat_dto:
                self._session.delete(chat_dto)
                self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e
