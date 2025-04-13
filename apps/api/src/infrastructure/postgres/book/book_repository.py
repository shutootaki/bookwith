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

    def save(self, book: Book) -> None:
        try:
            existing_book = self._session.query(BookDTO).filter(BookDTO.id == book.id.value).first()

            if existing_book:
                orm_dict = BookDTO.to_orm_dict(book)
                for key, value in orm_dict.items():
                    setattr(existing_book, key, value)

                # アノテーションの更新処理
                if hasattr(book, "_annotations") and book._annotations is not None:
                    # 既存のアノテーションを取得
                    existing_annotations = self._session.query(AnnotationDTO).filter(AnnotationDTO.book_id == book.id.value).all()
                    existing_ids = {a.id for a in existing_annotations}
                    new_ids = {a.get("id") for a in book._annotations if a.get("id")}

                    # 削除対象のアノテーションを削除
                    if existing_ids - new_ids:
                        self._session.query(AnnotationDTO).filter(AnnotationDTO.id.in_(existing_ids - new_ids)).delete(synchronize_session=False)

                    # 更新対象のアノテーションを更新
                    to_update = [a for a in book._annotations if a.get("id") and a.get("id") in existing_ids]
                    for annotation in to_update:
                        self._session.query(AnnotationDTO).filter(AnnotationDTO.id == annotation.get("id")).update(annotation)

                    # 新規作成対象のアノテーションを作成
                    to_create = [a for a in book._annotations if not (a.get("id") and a.get("id") in existing_ids)]
                    if to_create:
                        self._session.bulk_save_objects([AnnotationDTO(**a) for a in to_create])
            else:
                book_orm = BookDTO.from_entity(book)
                self._session.add(book_orm)

                # 新規作成時にアノテーションも一緒に作成
                if hasattr(book, "_annotations") and book._annotations is not None and book._annotations:
                    for annotation in book._annotations:
                        # book_idが設定されていない場合は設定する
                        if "book_id" not in annotation:
                            annotation["book_id"] = book.id.value
                        self._session.add(AnnotationDTO(**annotation))

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
        book_orms = self._session.query(BookDTO).filter(BookDTO.deleted_at == None).options(joinedload(BookDTO.annotations)).all()

        books = []
        for book_orm in book_orms:
            books.append(book_orm.to_entity())
        return books

    def find_by_user_id(self, user_id: str) -> list[Book]:
        book_orms = (
            self._session.query(BookDTO).filter(BookDTO.user_id == user_id, BookDTO.deleted_at == None).options(joinedload(BookDTO.annotations)).all()
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

            # 更新対象のレコード数を取得
            update_count = (
                self._session.query(BookDTO)
                .filter(BookDTO.id.in_(id_values), BookDTO.deleted_at == None)
                .update(
                    {"deleted_at": now, "updated_at": now},
                    synchronize_session=False,
                )
            )

            # 削除された書籍IDを特定（実際に更新されたIDを取得する方法は複雑になるため、
            # ここではupdate_count > 0 かどうかで判断し、引数のIDリストを基に返す）
            # 厳密に削除されたIDのみ返したい場合は、更新前にIDを取得するなどの工夫が必要
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
