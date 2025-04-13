"""書籍関連のAPIスキーマ定義
リクエストおよびレスポンスのモデルを定義します
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.domain.book.entities.book import Book


class BookCreateRequest(BaseModel):
    """書籍作成リクエストモデル"""

    user_id: str = Field(..., description="ユーザーID")
    file_data: str = Field(..., description="Base64エンコードされたファイルデータ")
    file_name: str = Field(..., description="ファイル名")
    book_id: str | None = Field(None, description="書籍ID（指定がない場合は自動生成）")
    book_name: str | None = Field(None, description="書籍名（指定がない場合はファイル名）")
    cover_image: str | None = Field(None, description="Base64エンコードされたカバー画像データ")
    book_metadata: str | None = Field(None, description="書籍のメタデータ（JSON文字列）")


# class BookUpdateRequest(BaseModel):
#     """書籍更新リクエストモデル"""

#     annotations: Optional[List[Annotation]] = None
#     author: Optional[str] = None
#     book_metadata: Optional[Dict[str, Any]] = None
#     cfi: Optional[str] = None
#     configuration: Optional[Dict[str, Any]] = None
#     cover_path: Optional[str] = None
#     definitions: Optional[List[str]] = None
#     is_deleted: Optional[bool] = None
#     name: Optional[str] = None
#     percentage: Optional[float] = None

#     @field_validator("percentage")
#     def validate_percentage(cls, v):
#         if v is not None:
#             # 小数値が送信された場合、内部的には整数として扱う
#             return int(v)
#         return v


class BookUpdateRequest(BaseModel):
    class Annotation(BaseModel):
        """アノテーションモデル"""

        class AnnotationType(str, Enum):
            """アノテーションタイプ列挙型"""

            highlight = "highlight"

        class AnnotationColor(str, Enum):
            """アノテーション色列挙型"""

            yellow = "yellow"
            red = "red"
            green = "green"
            blue = "blue"

        """アノテーションモデル"""

        id: str
        book_id: str = Field(alias="bookId")
        cfi: str
        spine: dict[str, Any]
        type: AnnotationType
        color: AnnotationColor
        notes: str | None = None
        text: str

        class Config:
            from_attributes = True
            populate_by_name = True

    """書籍更新リクエストモデル"""

    name: str | None = Field(None, description="書籍名")
    author: str | None = Field(None, description="著者名")
    cfi: str | None = Field(None, description="現在の読書位置（CFI）")
    percentage: float | None = Field(None, description="読書進捗率（%）")
    annotations: list[Annotation] | None = Field(None, description="注釈情報")
    book_metadata: dict[str, Any] | None = Field(None, description="書籍のメタデータ")
    definitions: list[dict[str, Any]] | None = Field(None, description="ユーザー定義情報")
    configuration: dict[str, Any] | None = Field(None, description="書籍設定情報")


class BookDetail(BaseModel):
    """書籍詳細モデル"""

    id: str
    user_id: str
    name: str
    author: str | None = None
    file_path: str
    cover_path: str | None = None
    size: int
    cfi: str | None = None
    percentage: float = 0
    book_metadata: dict[str, Any] | None = {}
    definitions: list[dict[str, Any]] = []
    configuration: dict[str, Any] | None = {}
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    class Config:
        orm_mode = True
        from_attributes = True


class BookResponse(BaseModel):
    """書籍レスポンスモデル"""

    success: bool
    data: BookDetail
    message: str | None = None


class BooksResponse(BaseModel):
    """書籍一覧レスポンスモデル"""

    success: bool
    data: list[BookDetail]
    count: int
    message: str | None = None


class BookFileResponse(BaseModel):
    """書籍ファイルレスポンスモデル"""

    success: bool
    url: str
    message: str | None = None


class BulkDeleteResponse(BaseModel):
    """一括削除レスポンスモデル"""

    success: bool
    deletedIds: list[str]
    count: int
    message: str | None = None


def entity_to_detail(book: Book) -> BookDetail:
    """ドメインエンティティからAPIレスポンスモデルに変換する"""
    return BookDetail(
        id=book.id.value,
        user_id=book.user_id,
        name=book.title.value,
        author=book.author,
        file_path=book.file_path,
        cover_path=book.cover_path,
        size=book.size,
        cfi=book.cfi,
        percentage=book.percentage,
        book_metadata=book.book_metadata,
        definitions=book.definitions,
        configuration=book.configuration,
        created_at=book.created_at,
        updated_at=book.updated_at,
        deleted_at=book.deleted_at,
    )
