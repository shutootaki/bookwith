from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.config.app_config import TEST_USER_ID
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
    get_find_books_usecase,
    get_update_book_usecase,
)
from src.infrastructure.external.gcs import GCSClient
from src.presentation.api.error_messages.book_error_message import (
    BOOK_ACCESS_DENIED,
    BOOK_ALREADY_COMPLETED,
    BOOK_ALREADY_STARTED,
    BOOK_BULK_DELETE_ERROR,
    BOOK_COVER_FETCH_ERROR,
    BOOK_COVER_NOT_FOUND,
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
)
from src.usecase.book.create_book_usecase import CreateBookUseCase
from src.usecase.book.delete_book_usecase import (
    BulkDeleteBooksUseCase,
    DeleteBookUseCase,
)
from src.usecase.book.find_book_by_id_usecase import FindBookByIdUseCase
from src.usecase.book.find_books_usecase import (
    FindBooksByUserIdUseCase,
    FindBooksUseCase,
)
from src.usecase.book.update_book_usecase import UpdateBookUseCase

# Router configuration
router = APIRouter(prefix="/books", tags=["book"])


# Error handling utility function
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
        return HTTPException(status_code=400, detail=str(e))
    return HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=BooksResponse)
async def get_books(
    find_books_usecase: FindBooksUseCase = Depends(get_find_books_usecase),
):
    try:
        books = find_books_usecase.execute()
        book_details = [BookDetail(**book.model_dump(mode="json")) for book in books]
        return BooksResponse(success=True, data=book_details, count=len(book_details))
    except Exception as e:
        raise handle_domain_exception(e)


@router.get("/user/{user_id}", response_model=BooksResponse)
async def get_books_by_user(
    user_id: str,
    find_books_by_user_id_usecase: FindBooksByUserIdUseCase = Depends(get_find_books_by_user_id_usecase),
):
    try:
        books = find_books_by_user_id_usecase.execute(user_id)
        book_details = [BookDetail(**book.model_dump(mode="json")) for book in books]
        return BooksResponse(success=True, data=book_details, count=len(book_details))
    except Exception as e:
        raise handle_domain_exception(e)


@router.get("/covers")
async def get_covers(
    user_id: str = TEST_USER_ID,
    find_books_by_user_id_usecase: FindBooksByUserIdUseCase = Depends(get_find_books_by_user_id_usecase),
):
    try:
        books = find_books_by_user_id_usecase.execute(user_id)
        gcs_client = GCSClient()

        book_covers = []

        for book in books:
            if not book.cover_path:
                continue

            path = book.cover_path.replace(f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/", "")

            # 署名付きURLを生成
            bucket = gcs_client.get_client().bucket(gcs_client.bucket_name)
            blob = bucket.blob(path)
            cover_url = blob.generate_signed_url(version="v4", expiration=3600, method="GET") if not gcs_client.use_emulator else book.cover_path

            book_covers.append(
                {
                    "book_id": book.id.value,
                    "name": book.name.value,
                    "cover_url": cover_url,
                }
            )

        return {"success": True, "data": book_covers}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=BOOK_COVER_FETCH_ERROR.format(error=str(e)),
        )


@router.delete("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_books_endpoint(
    body: BulkDeleteRequestBody,
    bulk_delete_books_usecase: BulkDeleteBooksUseCase = Depends(get_bulk_delete_books_usecase),
):
    try:
        deleted_ids = bulk_delete_books_usecase.execute(body.book_ids)
        return BulkDeleteResponse(success=True, deleted_ids=deleted_ids, count=len(deleted_ids))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=BOOK_BULK_DELETE_ERROR.format(error=str(e)),
        )


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    find_book_by_id_usecase: FindBookByIdUseCase = Depends(get_find_book_by_id_usecase),
):
    try:
        book = find_book_by_id_usecase.execute(book_id)
        return BookResponse(success=True, data=BookDetail(**book.model_dump(mode="json")))
    except Exception as e:
        raise handle_domain_exception(e)


@router.get("/{book_id}/cover")
async def get_book_cover(
    book_id: str,
    user_id: str,
    find_book_by_id_usecase: FindBookByIdUseCase = Depends(get_find_book_by_id_usecase),
):
    try:
        book = find_book_by_id_usecase.execute(book_id)

        if not book.cover_path:
            raise HTTPException(status_code=404, detail=BOOK_COVER_NOT_FOUND)

        # Ownership verification
        if book.user_id != user_id:
            raise BookPermissionDeniedException

        gcs_client = GCSClient()

        if gcs_client.use_emulator:
            # Return direct URL in emulator environment
            return JSONResponse(content={"cover_path": book.cover_path})
        # Generate signed URL in production environment
        path = book.cover_path.replace(f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/", "")

        # Generate signed URL
        bucket = gcs_client.get_client().bucket(gcs_client.bucket_name)
        blob = bucket.blob(path)
        signed_url = blob.generate_signed_url(version="v4", expiration=3600, method="GET")

        return JSONResponse(content={"cover_path": signed_url})

    except BookPermissionDeniedException:
        raise HTTPException(status_code=403, detail=BOOK_ACCESS_DENIED)
    except BookNotFoundException:
        raise HTTPException(status_code=404, detail=BOOK_NOT_FOUND)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=SIGNED_URL_GENERATION_ERROR.format(error=str(e)),
        )


@router.get("/{book_id}/file", response_model=BookFileResponse)
async def get_book_file(
    book_id: str,
    user_id: str,
    find_book_by_id_usecase: FindBookByIdUseCase = Depends(get_find_book_by_id_usecase),
):
    try:
        book = find_book_by_id_usecase.execute(book_id)

        if not book.file_path:
            raise BookFileNotFoundException

        # Ownership verification
        if book.user_id != user_id:
            raise BookPermissionDeniedException

        gcs_client = GCSClient()

        if gcs_client.use_emulator:
            return BookFileResponse(success=True, url=book.file_path)
        path = book.file_path.replace(f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/", "")

        # Generate signed URL
        bucket = gcs_client.get_client().bucket(gcs_client.bucket_name)
        blob = bucket.blob(path)
        signed_url = blob.generate_signed_url(version="v4", expiration=3600, method="GET")

        return BookFileResponse(success=True, url=signed_url)

    except BookFileNotFoundException:
        raise HTTPException(status_code=404, detail=BOOK_FILE_NOT_FOUND)
    except BookPermissionDeniedException:
        raise HTTPException(status_code=403, detail=BOOK_ACCESS_DENIED)
    except BookNotFoundException:
        raise HTTPException(status_code=404, detail=BOOK_NOT_FOUND)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=SIGNED_URL_GENERATION_ERROR.format(error=str(e)),
        )


@router.post("", response_model=BookResponse)
async def post_book(
    body: BookCreateRequest,
    create_book_usecase: CreateBookUseCase = Depends(get_create_book_usecase),
):
    try:
        book = create_book_usecase.execute(
            user_id=body.user_id,
            file_name=body.file_name,
            file_data=body.file_data,
            book_name=body.book_name,
            cover_image=body.cover_image,
            book_metadata=body.book_metadata,
        )

        return BookResponse(
            success=True,
            data=BookDetail(**book.model_dump(mode="json")),
            message="Book successfully added",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=BOOK_CREATE_ERROR.format(error=str(e)),
        )


@router.put("/{book_id}")
async def put_book(
    book_id: str,
    changes: BookUpdateRequest,
    update_book_usecase: UpdateBookUseCase = Depends(get_update_book_usecase),
):
    try:
        book = update_book_usecase.execute(
            book_id=book_id,
            name=changes.name,
            author=changes.author,
            cfi=changes.cfi,
            percentage=changes.percentage,
            annotations=changes.annotations,
            book_metadata=changes.book_metadata,
            definitions=changes.definitions,
            configuration=changes.configuration,
        )

        return BookResponse(
            success=True,
            data=BookDetail(**book.model_dump(mode="json")),
            message="Book successfully updated",
        )
    except BookNotFoundException:
        raise HTTPException(status_code=404, detail=BOOK_NOT_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=BOOK_UPDATE_ERROR.format(error=str(e)),
        )


@router.delete("/{book_id}")
async def delete_book(
    book_id: str,
    delete_book_usecase: DeleteBookUseCase = Depends(get_delete_book_usecase),
):
    try:
        delete_book_usecase.execute(book_id)
        return JSONResponse(
            content={
                "success": True,
                "message": "Book successfully deleted",
            }
        )
    except BookNotFoundException:
        raise HTTPException(status_code=404, detail=BOOK_NOT_FOUND)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=BOOK_DELETE_ERROR.format(error=str(e)),
        )
