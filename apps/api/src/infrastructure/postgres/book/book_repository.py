from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from src.domain.book.entities.book import Book
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.infrastructure.postgres.annotation.annotation_dto import AnnotationDTO
from src.infrastructure.postgres.book.book_dto import BookDTO


class PostgresBookRepository(BookRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, book: Book) -> None:  # noqa: C901
        try:
            existing_book = self._session.query(BookDTO).filter(BookDTO.id == book.id.value).first()

            if existing_book:
                for key, value in BookDTO.to_orm_dict(book).items():
                    setattr(existing_book, key, value)

                if hasattr(book, "_annotations") and book._annotations is not None:
                    existing_annotations = self._session.query(AnnotationDTO).filter(AnnotationDTO.book_id == book.id.value).all()
                    existing_ids = {a.id for a in existing_annotations}
                    new_ids = {a.get("id") for a in book._annotations if a.get("id")}

                    if ids_to_delete := existing_ids - new_ids:
                        self._session.query(AnnotationDTO).filter(AnnotationDTO.id.in_(ids_to_delete)).delete(synchronize_session=False)

                    to_update = [a for a in book._annotations if a.get("id") in existing_ids]
                    if to_update:
                        anno_map = {
                            a.id: a for a in self._session.query(AnnotationDTO).filter(AnnotationDTO.id.in_([a.get("id") for a in to_update])).all()
                        }

                        for annotation in to_update:
                            if anno_obj := anno_map.get(annotation.get("id")):
                                for key, value in AnnotationDTO.from_dict(annotation).items():
                                    setattr(anno_obj, key, value)

                    to_create = [a for a in book._annotations if not a.get("id") or a.get("id") not in existing_ids]
                    if to_create:
                        self._session.bulk_save_objects(
                            [AnnotationDTO(**AnnotationDTO.from_dict({**a.copy(), "book_id": book.id.value})) for a in to_create]
                        )
            else:
                self._session.add(BookDTO.from_entity(book))

                if hasattr(book, "_annotations") and book._annotations:
                    self._session.bulk_save_objects(
                        [AnnotationDTO(**AnnotationDTO.from_dict({**a.copy(), "book_id": book.id.value})) for a in book._annotations]
                    )

            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e

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
