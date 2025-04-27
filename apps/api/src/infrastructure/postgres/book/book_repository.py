from datetime import datetime
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session, joinedload

from src.domain.book.entities.book import Book
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.infrastructure.postgres.annotation.annotation_dto import AnnotationDTO
from src.infrastructure.postgres.book.book_dto import BookDTO


class PostgresBookRepository(BookRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, book: Book) -> None:
        session = self._session

        def flatten(d: dict[str, Any]) -> dict[str, Any]:
            return {k: (v["value"] if isinstance(v, dict) and "value" in v else v) for k, v in d.items()}

        # --- upsert Book ---
        book_data = flatten(book.model_dump(mode="json"))
        dto = session.get(BookDTO, book.id.value)
        col_keys = {c.key for c in inspect(BookDTO).mapper.column_attrs}

        if dto:
            for k, v in book_data.items():
                if k in col_keys:
                    setattr(dto, k, v)
        else:
            session.add(BookDTO(**book_data))

        # --- sync Annotations ---
        ann_objs = book.annotations or []
        existing_ids = {id_ for (id_,) in session.query(AnnotationDTO.id).filter_by(book_id=book.id.value)}
        incoming_ids = {a.id.value for a in ann_objs}

        # delete removed
        to_delete = existing_ids - incoming_ids
        if to_delete:
            session.query(AnnotationDTO).filter(AnnotationDTO.id.in_(to_delete)).delete(synchronize_session=False)

        to_update = [a for a in book.annotations if a.id and a.id.value in existing_ids]
        if to_update:
            update_mappings = []
            for a in to_update:
                update_mappings.append(AnnotationDTO.enum_name_safe(a))

            if update_mappings:
                self._session.bulk_update_mappings(
                    inspect(AnnotationDTO),
                    update_mappings,
                )

        to_create = [a for a in book.annotations if not a.id.value or a.id.value not in existing_ids]
        if to_create:
            self._session.bulk_save_objects([AnnotationDTO.from_dict(a.model_dump(mode="json")) for a in to_create])

        session.commit()

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

    def find_all(self) -> list[Book]:
        book_orms = (
            self._session.query(BookDTO)
            .filter(BookDTO.deleted_at == None)
            .options(joinedload(BookDTO.annotations))
            .order_by(BookDTO.updated_at.desc())
            .all()
        )

        books = []
        for book_orm in book_orms:
            books.append(book_orm.to_entity())
        return books

    def find_by_user_id(self, user_id: str) -> list[Book]:
        book_orms = (
            self._session.query(BookDTO)
            .filter(BookDTO.user_id == user_id, BookDTO.deleted_at == None)
            .options(joinedload(BookDTO.annotations))
            .order_by(BookDTO.updated_at.desc())
            .all()
        )

        return [book_orm.to_entity() for book_orm in book_orms]

    def delete(self, book_id: BookId) -> None:
        now = datetime.now()
        try:
            result = (
                self._session.query(BookDTO)
                .filter(BookDTO.id == book_id.value, BookDTO.deleted_at == None)
                .update({"deleted_at": now, "updated_at": now})
            )

            if result > 0:
                self._session.commit()
            else:
                self._session.rollback()
        except Exception as e:
            self._session.rollback()
            raise e

    def bulk_delete(self, book_ids: list[BookId]) -> list[BookId]:
        if not book_ids:
            return []

        try:
            now = datetime.now()
            id_values = [book_id.value for book_id in book_ids]

            update_count = (
                self._session.query(BookDTO)
                .filter(BookDTO.id.in_(id_values), BookDTO.deleted_at == None)
                .update(
                    {"deleted_at": now, "updated_at": now},
                    synchronize_session=False,
                )
            )

            deleted_ids = []
            if update_count > 0:
                deleted_ids = [BookId(bid) for bid in id_values]
                self._session.commit()
            else:
                self._session.rollback()

            return deleted_ids

        except Exception as e:
            self._session.rollback()
            raise e
