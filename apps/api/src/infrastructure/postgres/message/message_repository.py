from datetime import datetime

from sqlalchemy import func, update
from sqlalchemy.orm import Session

from src.domain.message.entities.message import Message
from src.domain.message.repositories.message_repository import MessageRepository
from src.domain.message.value_objects.message_id import MessageId
from src.infrastructure.postgres.chat.chat_dto import ChatDTO
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
        except Exception:
            self._session.rollback()
            raise

    def find_by_id(self, message_id: MessageId) -> Message | None:
        message_orm = self._session.query(MessageDTO).filter(MessageDTO.id == message_id.value, MessageDTO.deleted_at == None).first()

        if not message_orm:
            return None

        return message_orm.to_entity()

    def find_by_id_for_user(self, message_id: MessageId, user_id: str) -> Message | None:
        # CR-3: メッセージが属するチャットの user_id で絞り込む。
        message_orm = (
            self._session.query(MessageDTO)
            .join(ChatDTO, ChatDTO.id == MessageDTO.chat_id)
            .filter(
                MessageDTO.id == message_id.value,
                MessageDTO.deleted_at == None,
                ChatDTO.user_id == user_id,
                ChatDTO.deleted_at == None,
            )
            .first()
        )

        if not message_orm:
            return None
        return message_orm.to_entity()

    def find_by_chat_id(self, chat_id: str) -> list[Message]:
        message_orms = (
            self._session.query(MessageDTO)
            .filter(MessageDTO.chat_id == chat_id, MessageDTO.deleted_at == None)
            .order_by(MessageDTO.created_at.asc())
            .all()
        )

        return [message_orm.to_entity() for message_orm in message_orms]

    def find_by_chat_id_for_user(self, chat_id: str, user_id: str) -> list[Message]:
        # H-16: チャットの所有者検証を join で組み込む。
        message_orms = (
            self._session.query(MessageDTO)
            .join(ChatDTO, ChatDTO.id == MessageDTO.chat_id)
            .filter(
                MessageDTO.chat_id == chat_id,
                MessageDTO.deleted_at == None,
                ChatDTO.user_id == user_id,
                ChatDTO.deleted_at == None,
            )
            .order_by(MessageDTO.created_at.asc())
            .all()
        )
        return [message_orm.to_entity() for message_orm in message_orms]

    def find_latest_by_chat_id(self, chat_id: str, limit: int) -> list[Message]:
        """チャットIDで最新のメッセージを指定件数取得する."""
        message_orms = (
            self._session.query(MessageDTO)
            .filter(MessageDTO.chat_id == chat_id, MessageDTO.deleted_at == None)
            .order_by(MessageDTO.created_at.desc())  # 新しい順（降順）
            .limit(limit)
            .all()
        )

        return [message_orm.to_entity() for message_orm in message_orms]

    def find_latest_by_chat_id_for_user(self, chat_id: str, limit: int, user_id: str) -> list[Message]:
        message_orms = (
            self._session.query(MessageDTO)
            .join(ChatDTO, ChatDTO.id == MessageDTO.chat_id)
            .filter(
                MessageDTO.chat_id == chat_id,
                MessageDTO.deleted_at == None,
                ChatDTO.user_id == user_id,
                ChatDTO.deleted_at == None,
            )
            .order_by(MessageDTO.created_at.desc())
            .limit(limit)
            .all()
        )
        return [message_orm.to_entity() for message_orm in message_orms]

    def delete_for_user(self, message_id: MessageId, user_id: str) -> bool:
        now = datetime.now()
        try:
            owned_id = (
                self._session.query(MessageDTO.id)
                .join(ChatDTO, ChatDTO.id == MessageDTO.chat_id)
                .filter(
                    MessageDTO.id == message_id.value,
                    MessageDTO.deleted_at == None,
                    ChatDTO.user_id == user_id,
                    ChatDTO.deleted_at == None,
                )
                .first()
            )
            if owned_id is None:
                return False

            self._session.query(MessageDTO).filter(MessageDTO.id == message_id.value).update({"deleted_at": now, "updated_at": now})
            self._session.commit()
            return True
        except Exception:
            self._session.rollback()
            raise

    def bulk_delete_for_user(self, message_ids: list[MessageId], user_id: str) -> list[MessageId]:
        if not message_ids:
            return []

        try:
            now = datetime.now()
            id_values = [message_id.value for message_id in message_ids]

            # 所有チェック (chat 経由) と論理削除を 1 回の UPDATE ... RETURNING に纏める。
            owned_chat_ids = self._session.query(ChatDTO.id).filter(ChatDTO.user_id == user_id, ChatDTO.deleted_at == None)
            stmt = (
                update(MessageDTO)
                .where(
                    MessageDTO.id.in_(id_values),
                    MessageDTO.deleted_at == None,
                    MessageDTO.chat_id.in_(owned_chat_ids),
                )
                .values(deleted_at=now, updated_at=now)
                .returning(MessageDTO.id)
            )
            result = self._session.execute(stmt)
            deleted_ids = [row[0] for row in result.all()]
            self._session.commit()
            return [MessageId(mid) for mid in deleted_ids]

        except Exception:
            self._session.rollback()
            raise

    def count_by_chat_id(self, chat_id: str) -> int:
        """チャットIDに関連するメッセージの数を取得する."""
        try:
            count = self._session.query(func.count(MessageDTO.id)).filter(MessageDTO.chat_id == chat_id, MessageDTO.deleted_at == None).scalar()
            return count or 0
        except Exception:
            return 0
