import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

import weaviate
from fastapi import UploadFile
from langchain_community.document_loaders import UnstructuredEPubLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_weaviate.vectorstores import WeaviateVectorStore


class CreateBookVectorIndexUseCase(ABC):
    @abstractmethod
    async def execute(self, file: UploadFile, tenant_id: str) -> dict:
        """EPUBファイルを処理してベクトルストアにインデックス化する"""


class CreateBookVectorIndexUseCaseImpl(CreateBookVectorIndexUseCase):
    def __init__(self) -> None:
        pass

    async def execute(self, file: UploadFile, tenant_id: str) -> dict:
        try:
            with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as temp_file:
                file_content = await file.read()
                temp_file.write(file_content)
                temp_path = temp_file.name

            try:
                docs = UnstructuredEPubLoader(temp_path).load()

                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                split_docs = splitter.split_documents(docs)

                WeaviateVectorStore.from_documents(
                    documents=split_docs,
                    embedding=OpenAIEmbeddings(
                        model="text-embedding-3-large",
                        max_retries=2,
                    ),
                    client=weaviate.connect_to_local(),
                    index_name="BookContentIndex",
                    text_key="content",
                    tenant=tenant_id,
                )

                return {
                    "message": "Upload and processing completed successfully",
                    "file_name": file.filename,
                    "chunk_count": len(split_docs),
                    "index_name": "BookContentIndex",
                    "tenant_id": tenant_id,
                    "success": True,
                }
            finally:
                Path(temp_path).unlink(missing_ok=True)

        except Exception as e:
            raise ValueError(f"Error occurred during vector indexing: {str(e)}")
