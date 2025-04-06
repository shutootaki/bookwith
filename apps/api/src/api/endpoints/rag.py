from fastapi import APIRouter, File, Form, UploadFile
from src.models import RagProcessResponse
from src.services import process_epub_file
from src.utils import BadRequestException, ServiceUnavailableException

router = APIRouter()


@router.post("/rag", response_model=RagProcessResponse)
async def upload_and_process_rag(
    user_id: str = Form(...), book_id: str = Form(...), file: UploadFile = File(...)
):
    try:
        # ユーザーIDをプロセス関数に渡す
        return await process_epub_file(file, user_id, book_id)
    except ValueError as e:
        # ファイル形式や内容に関するエラーの場合
        raise BadRequestException(str(e))
    except Exception as e:
        # その他のエラーの場合
        raise ServiceUnavailableException(
            f"Error occurred while processing file: {str(e)}"
        )
