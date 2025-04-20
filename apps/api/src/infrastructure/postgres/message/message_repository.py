from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.domain.message.entities.message import Message
from src.domain.message.repositories.message_repository import MessageRepository
from src.domain.message.value_objects.message_id import MessageId
from src.infrastructure.postgres.message.message_dto import MessageDTO


class MessageRepositoryImpl(MessageRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, message: Message) -> None:
        try:
            existing_message = self._session.query(MessageDTO).filter(MessageDTO.id == message.id.value).first()

            if existing_message:
                orm_dict = MessageDTO.to_orm_dict(message)
                for key, value in orm_dict.items():
                    setattr(existing_message, key, value)
            else:
                message_orm = MessageDTO.from_entity(message)
                self._session.add(message_orm)

            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e

    def find_by_id(self, message_id: MessageId) -> Message | None:
        message_orm = self._session.query(MessageDTO).filter(MessageDTO.id == message_id.value, MessageDTO.deleted_at == None).first()

        if not message_orm:
            return None

        return message_orm.to_entity()

    def find_all(self) -> list[Message]:
        message_orms = self._session.query(MessageDTO).filter(MessageDTO.deleted_at == None).all()

        return [message_orm.to_entity() for message_orm in message_orms]

    def find_by_chat_id(self, chat_id: str) -> list[Message]:
        message_orms = (
            self._session.query(MessageDTO)
            .filter(MessageDTO.chat_id == chat_id, MessageDTO.deleted_at == None)
            .order_by(MessageDTO.created_at.asc())
            .all()
        )

        return [message_orm.to_entity() for message_orm in message_orms]

    def find_by_sender_id(self, sender_id: str) -> list[Message]:
        message_orms = self._session.query(MessageDTO).filter(MessageDTO.sender_id == sender_id, MessageDTO.deleted_at == None).all()

        return [message_orm.to_entity() for message_orm in message_orms]

    def delete(self, message_id: MessageId) -> None:
        now = datetime.now()
        try:
            result = (
                self._session.query(MessageDTO)
                .filter(MessageDTO.id == message_id.value, MessageDTO.deleted_at == None)
                .update({"deleted_at": now, "updated_at": now})
            )

            if result > 0:
                self._session.commit()
            else:
                self._session.rollback()
        except Exception as e:
            self._session.rollback()
            raise e

    def bulk_delete(self, message_ids: list[MessageId]) -> list[MessageId]:
        if not message_ids:
            return []

        try:
            now = datetime.now()
            id_values = [message_id.value for message_id in message_ids]

            update_count = (
                self._session.query(MessageDTO)
                .filter(MessageDTO.id.in_(id_values), MessageDTO.deleted_at == None)
                .update(
                    {"deleted_at": now, "updated_at": now},
                    synchronize_session=False,
                )
            )

            deleted_ids = []
            if update_count > 0:
                deleted_ids = [MessageId(mid) for mid in id_values]
                self._session.commit()
            else:
                self._session.rollback()

            return deleted_ids

        except Exception as e:
            self._session.rollback()
            raise e

    def count_by_chat_id(self, chat_id: str) -> int:
        """チャットIDに関連するメッセージの数を取得する."""
        try:
            count = self._session.query(func.count(MessageDTO.id)).filter(MessageDTO.chat_id == chat_id, MessageDTO.deleted_at == None).scalar()
            return count or 0
        except Exception as e:
            print(f"メッセージカウント取得中にエラーが発生: {str(e)}")
            return 0
