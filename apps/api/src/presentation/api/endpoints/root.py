from fastapi import APIRouter
from src.application.schemas.base import RootResponse

router = APIRouter()


@router.get("/", response_model=RootResponse)
async def root():
    return RootResponse(message="BookWith FastAPI Server")
