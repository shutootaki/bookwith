import base64
import json
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from src.db import get_db
from src.models import BookBase, BookDetail, BookResponse, BooksResponse
from src.models.database import Book
from src.models.schemas import BookCreateRequest

router = APIRouter(prefix="/books", tags=["book"])


@router.get("", response_model=BooksResponse)
async def all_books(db: Session = Depends(get_db)):
    """全ての書籍を取得するエンドポイント"""
    try:
        books = db.query(Book).all()
        book_list = [BookBase.from_orm(book) for book in books]
        return BooksResponse(success=True, data=book_list, count=len(books))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"書籍の取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: str, db: Session = Depends(get_db)):
    """特定の書籍を取得するエンドポイント"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=404, detail=f"ID {book_id} の書籍が見つかりません"
        )

    return BookResponse(success=True, data=BookDetail.from_orm(book))


@router.get("/{book_id}/cover")
async def get_book_cover(book_id: str, db: Session = Depends(get_db)):
    """書籍のカバー画像を取得するエンドポイント"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=404, detail=f"ID {book_id} の書籍が見つかりません"
        )

    if not book.cover_path or not os.path.exists(book.cover_path):
        raise HTTPException(
            status_code=404, detail="この書籍にはカバー画像がありません"
        )

    return FileResponse(book.cover_path, media_type="image/jpeg")


@router.get("/{book_id}/file")
async def get_book_file(book_id: str, db: Session = Depends(get_db)):
    """書籍のEPUBファイルを取得するエンドポイント"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=404, detail=f"ID {book_id} の書籍が見つかりません"
        )

    if not book.file_path or not os.path.exists(book.file_path):
        raise HTTPException(
            status_code=404, detail="この書籍のファイルが見つかりません"
        )

    return FileResponse(
        book.file_path, media_type="application/epub+zip", filename=f"{book.name}"
    )


@router.post("", response_model=BookResponse)
async def create_book(body: BookCreateRequest, db: Session = Depends(get_db)):
    """新しい書籍を作成するエンドポイント"""
    try:
        # ユーザーディレクトリを作成
        user_dir = os.path.join("tmp", "books", body.user_id)
        os.makedirs(user_dir, exist_ok=True)

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

        # 書籍ディレクトリを作成
        book_dir = os.path.join(user_dir, book_id)
        os.makedirs(book_dir, exist_ok=True)

        # EPUBファイルパス
        file_path = os.path.join(book_dir, "book.epub")

        # Base64からファイルデータをデコードして保存
        file_data = base64.b64decode(body.file_data)
        with open(file_path, "wb") as f:
            f.write(file_data)

        # カバー画像を保存（もし提供されていれば）
        cover_path = None
        if body.cover_image and body.cover_image.startswith("data:image/"):
            try:
                # Base64データURLからデータを抽出
                image_data = body.cover_image.split(",")[1]
                image_binary = base64.b64decode(image_data)

                # カバー画像のパス
                cover_path = os.path.join(book_dir, "cover.jpg")

                # 画像を保存
                with open(cover_path, "wb") as cover_file:
                    cover_file.write(image_binary)
            except Exception as e:
                print(f"カバー画像の保存中にエラーが発生しました: {str(e)}")

        # ファイルサイズを取得
        file_size = os.path.getsize(file_path)

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
            data=BookDetail.from_orm(new_book),
            message="書籍が正常に追加されました",
        )
    except Exception as e:
        # エラー発生時はロールバック
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"書籍の作成中にエラーが発生しました: {str(e)}"
        )
