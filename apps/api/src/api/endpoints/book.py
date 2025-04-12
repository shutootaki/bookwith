from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from infra.external.gcs import BUCKET_NAME
from services.book_service import add_book
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
async def get_book_cover(
    book_id: str, current_user_id: str, db: Session = Depends(get_db)
):
    """書籍のカバー画像を取得するエンドポイント（署名付きURL）"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=404, detail=f"ID {book_id} の書籍が見つかりません"
        )

    if not book.cover_path:
        raise HTTPException(
            status_code=404, detail="この書籍にはカバー画像がありません"
        )

    # 所有権の検証
    if book.user_id != current_user_id:
        raise HTTPException(
            status_code=403, detail="この書籍へのアクセス権限がありません"
        )

    try:
        # GCSのパスからバケット名とオブジェクト名を抽出
        path = book.cover_path.replace(
            f"https://storage.googleapis.com/{BUCKET_NAME}/", ""
        )

        # 署名付きURLを生成
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(path)
        signed_url = blob.generate_signed_url(
            version="v4", expiration=timedelta(minutes=15), method="GET"
        )

        return JSONResponse(content={"success": True, "url": signed_url})
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"署名付きURLの生成中にエラーが発生しました: {str(e)}",
        )


@router.get("/{book_id}/file")
async def get_book_file(
    book_id: str, current_user_id: str, db: Session = Depends(get_db)
):
    """書籍のEPUBファイルを取得するエンドポイント（署名付きURL）"""
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
    if book.user_id != current_user_id:
        raise HTTPException(
            status_code=403, detail="この書籍へのアクセス権限がありません"
        )

    try:
        # GCSのパスからバケット名とオブジェクト名を抽出
        path = book.file_path.replace(
            f"https://storage.googleapis.com/{BUCKET_NAME}/", ""
        )

        # 署名付きURLを生成
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(path)
        signed_url = blob.generate_signed_url(
            version="v4", expiration=timedelta(minutes=15), method="GET"
        )

        return JSONResponse(content={"success": True, "url": signed_url})
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"署名付きURLの生成中にエラーが発生しました: {str(e)}",
        )


@router.post("", response_model=BookResponse)
async def post_book(body: BookCreateRequest, db: Session = Depends(get_db)):
    """新しい書籍を作成するエンドポイント"""
    try:
        return await add_book(body, db)
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"書籍の作成中にエラーが発生しました: {str(e)}"
        )
