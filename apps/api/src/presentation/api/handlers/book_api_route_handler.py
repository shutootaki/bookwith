import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.domain.book.exceptions.book_exceptions import (
    BookAlreadyCompletedException,
    BookAlreadyStartedException,
    BookDomainException,
    BookFileNotFoundException,
    BookNotFoundException,
    BookPermissionDeniedException,
)
from src.infrastructure.di.injection import (
    get_bulk_delete_books_usecase,
    get_create_book_usecase,
    get_delete_book_usecase,
    get_find_book_by_id_usecase,
    get_find_books_by_user_id_usecase,
    get_update_book_usecase,
)
from src.infrastructure.external.gcs import GCSClient
from src.presentation.api.auth import require_user_id
from src.presentation.api.error_messages.book_error_message import (
    BOOK_ACCESS_DENIED,
    BOOK_ALREADY_COMPLETED,
    BOOK_ALREADY_STARTED,
    BOOK_BULK_DELETE_ERROR,
    BOOK_COVER_FETCH_ERROR,
    BOOK_CREATE_ERROR,
    BOOK_DELETE_ERROR,
    BOOK_FILE_NOT_FOUND,
    BOOK_NOT_FOUND,
    BOOK_UPDATE_ERROR,
    SIGNED_URL_GENERATION_ERROR,
)
from src.presentation.api.schemas.book_schema import (
    BookCreateRequest,
    BookDetail,
    BookFileResponse,
    BookResponse,
    BooksResponse,
    BookUpdateRequest,
    BulkDeleteRequestBody,
    BulkDeleteResponse,
    CoversResponse,
)
from src.usecase.book.create_book_usecase import CreateBookUseCase
from src.usecase.book.delete_book_usecase import (
    BulkDeleteBooksUseCase,
    DeleteBookUseCase,
)
from src.usecase.book.find_book_by_id_usecase import FindBookByIdUseCase
from src.usecase.book.find_books_usecase import (
    FindBooksByUserIdUseCase,
)
from src.usecase.book.update_book_usecase import UpdateBookUseCase

logger = logging.getLogger(__name__)
router = APIRouter()


def handle_domain_exception(e: Exception) -> HTTPException:
    if isinstance(e, BookNotFoundException):
        return HTTPException(status_code=404, detail=BOOK_NOT_FOUND)
    if isinstance(e, BookPermissionDeniedException):
        return HTTPException(status_code=403, detail=BOOK_ACCESS_DENIED)
    if isinstance(e, BookFileNotFoundException):
        return HTTPException(status_code=404, detail=BOOK_FILE_NOT_FOUND)
    if isinstance(e, BookAlreadyStartedException):
        return HTTPException(status_code=400, detail=BOOK_ALREADY_STARTED)
    if isinstance(e, BookAlreadyCompletedException):
        return HTTPException(status_code=400, detail=BOOK_ALREADY_COMPLETED)
    if isinstance(e, BookDomainException):
        # ドメイン例外は固定文言ベースなのでメッセージを返してよい。
        return HTTPException(status_code=400, detail=str(e))
    # 内部例外を文字列化してレスポンスへ載せない (情報漏洩防止)。
    logger.exception("Unhandled exception in book handler")
    return HTTPException(status_code=500, detail=BOOK_UPDATE_ERROR)


####################################################
# Get
####################################################
@router.get("/me", response_model=BooksResponse)
async def get_my_books(
    user_id: str = Depends(require_user_id),
    find_books_by_user_id_usecase: FindBooksByUserIdUseCase = Depends(get_find_books_by_user_id_usecase),
):
    """認証ユーザーの全ての本を取得する."""
    try:
        books = find_books_by_user_id_usecase.execute(user_id)
        book_details = [BookDetail.from_entity(book) for book in books]
        return BooksResponse(books=book_details, count=len(book_details))
    except Exception as e:
        raise handle_domain_exception(e)


@router.get("/covers", response_model=CoversResponse)
async def get_covers(
    user_id: str = Depends(require_user_id),
    find_books_by_user_id_usecase: FindBooksByUserIdUseCase = Depends(get_find_books_by_user_id_usecase),
) -> CoversResponse:
    try:
        books = find_books_by_user_id_usecase.execute(user_id)
        gcs_client = GCSClient()

        book_covers = []

        for book in books:
            if not book.cover_path:
                continue

            path = gcs_client.strip_public_url_prefix(book.cover_path)
            cover_url = book.cover_path if gcs_client.use_emulator else gcs_client.generate_signed_get_url(path)

            book_covers.append(
                {
                    "book_id": book.id.value,
                    "name": book.name.value,
                    "cover_url": cover_url,
                }
            )

        return CoversResponse(covers=[CoversResponse.CoverData(**book_cover) for book_cover in book_covers])
    except Exception:
        logger.exception("Failed to fetch covers")
        raise HTTPException(status_code=500, detail=BOOK_COVER_FETCH_ERROR)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    user_id: str = Depends(require_user_id),
    find_book_by_id_usecase: FindBookByIdUseCase = Depends(get_find_book_by_id_usecase),
):
    try:
        book = find_book_by_id_usecase.execute(book_id, user_id)
        return BookResponse(book_detail=BookDetail.from_entity(book))
    except Exception as e:
        raise handle_domain_exception(e)


@router.get("/{book_id}/file", response_model=BookFileResponse)
async def get_book_file(
    book_id: str,
    user_id: str = Depends(require_user_id),
    find_book_by_id_usecase: FindBookByIdUseCase = Depends(get_find_book_by_id_usecase),
):
    try:
        book = find_book_by_id_usecase.execute(book_id, user_id)

        if not book.file_path:
            raise BookFileNotFoundException

        gcs_client = GCSClient()
        if gcs_client.use_emulator:
            return BookFileResponse(url=book.file_path)

        path = gcs_client.strip_public_url_prefix(book.file_path)
        return BookFileResponse(url=gcs_client.generate_signed_get_url(path))

    except BookFileNotFoundException:
        raise HTTPException(status_code=404, detail=BOOK_FILE_NOT_FOUND)
    except BookPermissionDeniedException:
        raise HTTPException(status_code=403, detail=BOOK_ACCESS_DENIED)
    except BookNotFoundException:
        raise HTTPException(status_code=404, detail=BOOK_NOT_FOUND)
    except Exception:
        logger.exception("Signed URL generation failed")
        raise HTTPException(status_code=500, detail=SIGNED_URL_GENERATION_ERROR)


####################################################
# Post
####################################################
@router.post("", response_model=BookResponse)
async def post_book(
    body: BookCreateRequest,
    user_id: str = Depends(require_user_id),
    create_book_usecase: CreateBookUseCase = Depends(get_create_book_usecase),
):
    try:
        # CR-4: クライアントの user_id を信頼せず、認証 principal から渡す。
        book = create_book_usecase.execute(
            user_id=user_id,
            file_name=body.file_name,
            file_data=body.file_data,
            book_name=body.book_name,
            cover_image=body.cover_image,
            book_metadata=body.book_metadata,
        )

        return BookResponse(book_detail=BookDetail.from_entity(book))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Failed to create book")
        raise HTTPException(status_code=500, detail=BOOK_CREATE_ERROR)


####################################################
# Put
####################################################
@router.put("/{book_id}")
async def put_book(
    book_id: str,
    changes: BookUpdateRequest,
    user_id: str = Depends(require_user_id),
    update_book_usecase: UpdateBookUseCase = Depends(get_update_book_usecase),
):
    try:
        book = update_book_usecase.execute(
            book_id=book_id,
            user_id=user_id,
            name=changes.name,
            author=changes.author,
            cfi=changes.cfi,
            percentage=changes.percentage,
            annotations=changes.annotations,
            book_metadata=changes.book_metadata,
            definitions=changes.definitions,
            configuration=changes.configuration,
        )

        return BookResponse(book_detail=BookDetail.from_entity(book))
    except BookPermissionDeniedException:
        raise HTTPException(status_code=403, detail=BOOK_ACCESS_DENIED)
    except BookNotFoundException:
        raise HTTPException(status_code=404, detail=BOOK_NOT_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Failed to update book")
        raise HTTPException(status_code=500, detail=BOOK_UPDATE_ERROR)


####################################################
# Delete
####################################################
@router.delete("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_books_endpoint(
    body: BulkDeleteRequestBody,
    user_id: str = Depends(require_user_id),
    bulk_delete_books_usecase: BulkDeleteBooksUseCase = Depends(get_bulk_delete_books_usecase),
):
    try:
        deleted_ids = bulk_delete_books_usecase.execute(body.book_ids, user_id)
        return BulkDeleteResponse(deleted_ids=deleted_ids, count=len(deleted_ids))
    except Exception:
        logger.exception("Bulk delete failed")
        raise HTTPException(status_code=500, detail=BOOK_BULK_DELETE_ERROR)


@router.delete("/{book_id}")
async def delete_book(
    book_id: str,
    user_id: str = Depends(require_user_id),
    delete_book_usecase: DeleteBookUseCase = Depends(get_delete_book_usecase),
):
    try:
        delete_book_usecase.execute(book_id, user_id)
        return JSONResponse(
            content={
                "success": True,
                "message": "Book successfully deleted",
            }
        )
    except BookPermissionDeniedException:
        raise HTTPException(status_code=403, detail=BOOK_ACCESS_DENIED)
    except BookNotFoundException:
        raise HTTPException(status_code=404, detail=BOOK_NOT_FOUND)
    except Exception:
        logger.exception("Failed to delete book")
        raise HTTPException(status_code=500, detail=BOOK_DELETE_ERROR)
