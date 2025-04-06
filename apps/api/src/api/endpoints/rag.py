from fastapi import APIRouter, File, HTTPException, UploadFile
from src.models import RagProcessResponse
from src.services import process_epub_file

router = APIRouter()


@router.post("/rag", response_model=RagProcessResponse)
async def upload_and_process_rag(file: UploadFile = File(...)):
    try:
        return await process_epub_file(file)
    except ValueError as e:
        print("Error during RAG processing:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print("Error during RAG processing:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
