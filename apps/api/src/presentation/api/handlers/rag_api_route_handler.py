import base64
import logging
from io import BytesIO

from fastapi import APIRouter, Depends, Request, UploadFile
from starlette.datastructures import Headers

from src.config.app_config import AppConfig
from src.domain.book.exceptions.book_exceptions import BookNotFoundException, BookPermissionDeniedException
from src.infrastructure.di.injection import get_create_book_vector_index_usecase, get_find_book_by_id_usecase
from src.presentation.api.auth import require_user_id
from src.presentation.api.error_messages.error_handlers import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    ServiceUnavailableException,
)
from src.presentation.api.middleware import expensive_limit
from src.presentation.api.schemas.book_schema import RagProcessRequest, RagProcessResponse
from src.usecase.book.create_book_vector_index_usecase import CreateBookVectorIndexUseCase
from src.usecase.book.find_book_by_id_usecase import FindBookByIdUseCase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=RagProcessResponse)
@expensive_limit()
async def upload_and_process_rag(
    request: Request,
    body: RagProcessRequest,
    user_id: str = Depends(require_user_id),
    find_book_by_id_usecase: FindBookByIdUseCase = Depends(get_find_book_by_id_usecase),
    usecase: CreateBookVectorIndexUseCase = Depends(get_create_book_vector_index_usecase),
):
    """Base64 で送られてきた EPUB をデコードし、ベクトルストアにインデックス化する."""
    try:
        # CR-3: 対象 book を所有しているか先に検証する。
        find_book_by_id_usecase.execute(body.book_id, user_id)

        # H-1 / M-3: サイズ上限チェック。base64 のデコード後で評価する。
        config = AppConfig.get_config()
        decoded_bytes = base64.b64decode(body.file_data)
        if len(decoded_bytes) > config.max_upload_bytes:
            raise BadRequestException("Uploaded file is too large")

        file_like = BytesIO(decoded_bytes)
        upload_file = UploadFile(
            file_like,
            filename=body.file_name,
            headers=Headers({"content-type": "application/epub+zip"}),
        )

        # CR-4: user_id は認証 principal から取得した値を渡す。
        return await usecase.execute(upload_file, user_id, body.book_id)
    except BookPermissionDeniedException:
        raise ForbiddenException()
    except BookNotFoundException:
        raise NotFoundException()
    except ValueError as e:
        raise BadRequestException(str(e))
    except Exception:
        # H-5: 例外文字列をレスポンスに直接含めない。
        logger.exception("RAG processing failed")
        raise ServiceUnavailableException("Error occurred while processing file")
