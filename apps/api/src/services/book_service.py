import base64
import json
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.infra.external.gcs import GCSClient
from src.models import BookDetail, BookResponse
from src.models.database import Book
from src.models.schemas import BookCreateRequest


def get_book_file_signed_url(book_id: str, user_id: str, db: Session):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=404, detail=f"ID {book_id} の書籍が見つかりません"
        )

    if not book.file_path:
        raise HTTPException(
            status_code=404, detail="この書籍のファイルが見つかりません"
        )

    # 所有権の検証
    if book.user_id != user_id:
        raise HTTPException(
            status_code=403, detail="この書籍へのアクセス権限がありません"
        )

    gcs_client = GCSClient()

    if gcs_client.use_emulator:
        return book.file_path
    else:
        path = book.file_path.replace(
            f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/", ""
        )

        # 署名付きURLを生成
        bucket = gcs_client.get_client().bucket(gcs_client.bucket_name)
        blob = bucket.blob(path)
        signed_url = (
            blob.generate_signed_url(
                version="v4", expiration=timedelta(minutes=15), method="GET"
            )
            if not gcs_client.use_emulator
            else book.file_path
        )
        return str(signed_url)


def get_all_covers(user_id: str, db: Session):
    gcs_client = GCSClient()

    # ユーザーが所有する書籍を取得
    books = db.query(Book).filter(Book.user_id == user_id).all()

    result = {"success": True, "data": []}

    for book in books:
        if not book.cover_path:
            continue

        path = book.cover_path.replace(
            f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/", ""
        )

        # 署名付きURLを生成
        bucket = gcs_client.get_client().bucket(gcs_client.bucket_name)
        blob = bucket.blob(path)
        cover_url = (
            blob.generate_signed_url(
                version="v4", expiration=timedelta(minutes=15), method="GET"
            )
            if not gcs_client.use_emulator
            else book.cover_path
        )

        result["data"].append(
            {"book_id": book.id, "name": book.name, "cover_url": cover_url}
        )

    return result


def all_books(db: Session):
    books = db.query(Book).filter(Book.deleted_at == None).all()
    book_list = [
        BookDetail.model_validate(book, from_attributes=True) for book in books
    ]
    return book_list


def add_book(body: BookCreateRequest, db: Session) -> BookResponse:
    try:
        # book_idが指定されていない場合は生成
        if not body.book_id:
            book_id = str(uuid.uuid4())
        else:
            book_id = body.book_id

        # ファイル名が指定されていない場合はアップロードされたファイル名を使用
        if not body.book_name:
            book_name = body.file_name
        else:
            book_name = body.book_name

        # Base64からファイルデータをデコード
        file_data = base64.b64decode(body.file_data)
        gcs_client = GCSClient()

        # GCSにアップロード
        bucket = gcs_client.get_client().bucket(gcs_client.bucket_name)
        epub_blob_name = f"books/{body.user_id}/{book_id}/book.epub"
        blob = bucket.blob(epub_blob_name)
        blob.upload_from_string(file_data, content_type="application/epub+zip")

        # ファイルパスを保存（GCSバケット上の実際のパスを保存）
        file_path = (
            f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/{epub_blob_name}"
        )

        # ファイルサイズを取得
        file_size = len(file_data)

        # カバー画像を保存（もし提供されていれば）
        cover_path = None
        if body.cover_image and body.cover_image.startswith("data:image/"):
            try:
                # Base64データURLからデータを抽出
                image_data = body.cover_image.split(",")[1]
                image_binary = base64.b64decode(image_data)

                # GCSにカバー画像をアップロード
                cover_blob_name = f"books/{body.user_id}/{book_id}/cover.jpg"
                cover_blob = bucket.blob(cover_blob_name)
                cover_blob.upload_from_string(image_binary, content_type="image/jpeg")

                # カバー画像のURLを設定
                cover_path = f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/{cover_blob_name}"
            except Exception as e:
                print(f"カバー画像の保存中にエラーが発生しました: {str(e)}")

        # メタデータがJSONとして渡された場合はパース
        metadata = {}
        if body.book_metadata:
            try:
                metadata = json.loads(body.book_metadata)
            except json.JSONDecodeError:
                pass

        new_book = Book(
            id=book_id,
            user_id=body.user_id,
            name=book_name,
            file_path=file_path,
            cover_path=cover_path,
            size=file_size,
            book_metadata=metadata,
            definitions=[],
            configuration={},
            author=metadata.get("creator", None),
        )

        db.add(new_book)
        db.commit()
        db.refresh(new_book)

        return BookResponse(
            success=True,
            data=BookDetail.model_validate(new_book, from_attributes=True),
            message="書籍が正常に追加されました",
        )
    except Exception:
        db.rollback()


def update_book(book_id: str, changes_dict: dict, db: Session) -> BookResponse:
    """書籍情報を更新する処理を行う関数"""
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=404, detail=f"ID {book_id} の書籍が見つかりません"
            )

        changes_dict["updated_at"] = datetime.now()

        for key, value in changes_dict.items():
            if hasattr(book, key):
                setattr(book, key, value)

        db.commit()
        db.refresh(book)

        return BookResponse(
            success=True, data=BookDetail.model_validate(book, from_attributes=True)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"書籍の更新中にエラーが発生しました: {str(e)}"
        )


def bulk_delete_books(book_ids: list[str], db: Session) -> dict:
    """複数の書籍を一括削除する処理を行う関数"""
    if not book_ids:
        return {"success": True, "deletedIds": [], "count": 0}

    try:
        now = datetime.now()
        existing_books = db.query(Book).filter(Book.id.in_(book_ids)).all()

        if not existing_books:
            return {"success": True, "deletedIds": [], "count": 0}

        existing_ids = [book.id for book in existing_books]
        mappings = [
            {"id": book_id, "is_deleted": True, "deleted_at": now, "updated_at": now}
            for book_id in existing_ids
        ]

        db.bulk_update_mappings(Book, mappings)

        gcs_client = GCSClient()
        bucket = gcs_client.get_client().bucket(gcs_client.bucket_name)

        for book in existing_books:
            print("パス", book.file_path)
            if book.file_path:
                file_path = book.file_path.replace(
                    f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/", ""
                )
                blob = bucket.blob(file_path)
                try:
                    blob.delete()
                except Exception as e:
                    print(f"書籍ファイルの削除中にエラーが発生しました: {str(e)}")

            if book.cover_path:
                cover_path = book.cover_path.replace(
                    f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/", ""
                )
                blob = bucket.blob(cover_path)
                try:
                    blob.delete()
                except Exception as e:
                    print(f"カバー画像の削除中にエラーが発生しました: {str(e)}")
        db.commit()

        return {"success": True, "deletedIds": existing_ids, "count": len(existing_ids)}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"書籍の一括削除中にエラーが発生しました: {str(e)}"
        )
