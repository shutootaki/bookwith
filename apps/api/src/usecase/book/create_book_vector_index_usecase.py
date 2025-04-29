from abc import ABC, abstractmethod

from fastapi import UploadFile

from src.infrastructure.memory.memory_vector_store import MemoryVectorStore


class CreateBookVectorIndexUseCase(ABC):
    @abstractmethod
    async def execute(self, file: UploadFile, user_id: str) -> dict:
        """EPUBファイルを処理してベクトルストアにインデックス化する."""


class CreateBookVectorIndexUseCaseImpl(CreateBookVectorIndexUseCase):
    def __init__(self) -> None:
        self.memory_vector_store = MemoryVectorStore()

    async def execute(self, file: UploadFile, user_id: str) -> dict:
        return await self.memory_vector_store.create_book_vector_index(file, user_id)
