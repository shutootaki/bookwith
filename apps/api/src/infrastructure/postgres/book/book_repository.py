from datetime import datetime

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, joinedload

from src.domain.book.entities.book import Book
from src.domain.book.repositories.book_repository import BookRepository as BookRepositoryInterface
from src.domain.book.value_objects.book_id import BookId
from src.infrastructure.memory.memory_service import MemoryService
from src.infrastructure.postgres.book.book_dto import BookDTO


class BookRepositoryImpl(BookRepositoryInterface):
    def __init__(
        self,
        session: Session,
        memory_service: MemoryService,
    ) -> None:
        self._session = session
        self.memory_service = memory_service

    def save(self, book: Book) -> None:
        session = self._session

        new_dto = BookDTO.from_entity(book)
        values = {column.name: getattr(new_dto, column.name) for column in BookDTO.__table__.columns}
        update_values = {k: v for k, v in values.items() if k not in {"id", "user_id", "created_at"}}
        # B-13: on_conflict_do_update で user_id まで上書きすると所有権が静かに移転するバグの素になるため除外。
        stmt = insert(BookDTO).values(**values).on_conflict_do_update(index_elements=[BookDTO.id], set_=update_values)

        try:
            session.execute(stmt)
            session.commit()
        except Exception:
            session.rollback()
            raise

    def find_by_id(self, book_id: BookId) -> Book | None:
        book_orm = (
            self._session.query(BookDTO)
            .filter(BookDTO.id == book_id.value, BookDTO.deleted_at == None)
            .options(joinedload(BookDTO.annotations))
            .first()
        )

        if not book_orm:
            return None

        return book_orm.to_entity()

    def find_by_id_for_user(self, book_id: BookId, user_id: str) -> Book | None:
        # CR-3: user_id を WHERE 句に必ず含める。
        book_orm = (
            self._session.query(BookDTO)
            .filter(
                BookDTO.id == book_id.value,
                BookDTO.user_id == user_id,
                BookDTO.deleted_at == None,
            )
            .options(joinedload(BookDTO.annotations))
            .first()
        )

        if not book_orm:
            return None

        return book_orm.to_entity()

    def find_by_ids_for_user(self, book_ids: list[BookId], user_id: str) -> list[Book]:
        if not book_ids:
            return []
        id_values = [book_id.value for book_id in book_ids]
        book_orms = (
            self._session.query(BookDTO)
            .filter(
                BookDTO.id.in_(id_values),
                BookDTO.user_id == user_id,
                BookDTO.deleted_at == None,
            )
            .options(joinedload(BookDTO.annotations))
            .all()
        )
        return [book_orm.to_entity() for book_orm in book_orms]

    def find_by_user_id(self, user_id: str) -> list[Book]:
        book_orms = (
            self._session.query(BookDTO)
            .filter(BookDTO.user_id == user_id, BookDTO.deleted_at == None)
            .options(joinedload(BookDTO.annotations))
            .order_by(BookDTO.updated_at.desc())
            .all()
        )

        return [book_orm.to_entity() for book_orm in book_orms]

    def delete_for_user(self, book_id: BookId, user_id: str) -> bool:
        now = datetime.now()
        try:
            result = (
                self._session.query(BookDTO)
                .filter(
                    BookDTO.id == book_id.value,
                    BookDTO.user_id == user_id,
                    BookDTO.deleted_at == None,
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

    def bulk_delete_for_user(self, book_ids: list[BookId], user_id: str) -> list[BookId]:
        if not book_ids:
            return []

        try:
            now = datetime.now()
            id_values = [book_id.value for book_id in book_ids]

            # 単一の UPDATE ... RETURNING で「所有・未削除のみ削除し、削除した id だけ返す」。
            # 旧実装は SELECT → UPDATE で 2 往復していた。
            stmt = (
                update(BookDTO)
                .where(
                    BookDTO.id.in_(id_values),
                    BookDTO.user_id == user_id,
                    BookDTO.deleted_at == None,
                )
                .values(deleted_at=now, updated_at=now)
                .returning(BookDTO.id)
            )
            result = self._session.execute(stmt)
            deleted_ids = [row[0] for row in result.all()]
            self._session.commit()
            return [BookId(bid) for bid in deleted_ids]

        except Exception:
            self._session.rollback()
            raise
