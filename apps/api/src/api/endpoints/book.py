from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.db import get_db
from src.infra.external.gcs import GCSClient
from src.models import BookDetail, BookResponse, BooksResponse
from src.models.database import Book
from src.models.schemas import BookCreateRequest, BookFileResponse
from src.services.book_service import (
    add_book,
    all_books,
    get_all_covers,
    get_book_file_signed_url,
)

router = APIRouter(prefix="/books", tags=["book"])


@router.get("", response_model=BooksResponse)
async def get_books(db: Session = Depends(get_db)):
    """全ての書籍を取得するエンドポイント"""
    try:
        book_list = all_books(db)
        return BooksResponse(success=True, data=book_list, count=len(book_list))
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"書籍の取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/covers", response_model=dict)
async def get_covers(user_id: str = "test_user_id", db: Session = Depends(get_db)):
    """ユーザーが所有するすべての書籍のカバー画像を取得するエンドポイント"""
    try:
        return get_all_covers(user_id, db)
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"書籍カバー画像の取得中にエラーが発生しました: {str(e)}",
        )


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: str, db: Session = Depends(get_db)):
    """特定の書籍を取得するエンドポイント"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=404, detail=f"ID {book_id} の書籍が見つかりません"
        )

    return BookResponse(
        success=True, data=BookDetail.model_validate(book, from_attributes=True)
    )


@router.get("/{book_id}/cover")
async def get_book_cover(book_id: str, user_id: str, db: Session = Depends(get_db)):
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
    if book.user_id != user_id:
        raise HTTPException(
            status_code=403, detail="この書籍へのアクセス権限がありません"
        )

    try:
        # AppConfigからエミュレーター環境かどうかを判定
        gcs_client = GCSClient()

        if gcs_client.use_emulator:
            # エミュレーター環境では直接URLを返す
            return JSONResponse(content={"cover_path": book.cover_path})
        else:
            # 本番環境では署名付きURLを生成
            # GCSのパスからバケット名とオブジェクト名を抽出
            path = book.cover_path.replace(
                f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/", ""
            )

            # 署名付きURLを生成
            bucket = gcs_client.get_client().bucket(gcs_client.bucket_name)
            blob = bucket.blob(path)
            signed_url = (
                blob.generate_signed_url(
                    version="v4", expiration=timedelta(minutes=15), method="GET"
                )
                if not GCSClient().use_emulator
                else book.cover_path
            )

            return JSONResponse(content={"cover_path": signed_url})
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"署名付きURLの生成中にエラーが発生しました: {str(e)}",
        )


@router.get("/{book_id}/file", response_model=BookFileResponse)
async def get_book_file(book_id: str, user_id: str, db: Session = Depends(get_db)):
    """書籍のEPUBファイルを取得するエンドポイント（署名付きURL）"""
    try:
        signed_url = get_book_file_signed_url(book_id, user_id, db)
        return BookFileResponse(success=True, url=signed_url)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"署名付きURLの生成中にエラーが発生しました: {str(e)}",
        )


@router.post("", response_model=BookResponse)
async def post_book(body: BookCreateRequest, db: Session = Depends(get_db)):
    """新しい書籍を作成するエンドポイント"""
    try:
        return add_book(body, db)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"書籍の作成中にエラーが発生しました: {str(e)}"
        )
