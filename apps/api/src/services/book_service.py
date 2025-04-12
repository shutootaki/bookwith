import base64
import json
import uuid
from datetime import timedelta

from sqlalchemy.orm import Session
from src.infra.external.gcs import GCSClient
from src.models import BookBase, BookDetail, BookResponse
from src.models.database import Book
from src.models.schemas import BookCreateRequest


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
    books = db.query(Book).all()
    book_list = [BookBase.model_validate(book, from_attributes=True) for book in books]
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

        # 書籍モデルを作成
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
        # データベースに保存
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
