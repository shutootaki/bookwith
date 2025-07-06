"""書籍コンテンツストア."""

import logging
import tempfile
from pathlib import Path

from fastapi import UploadFile
from langchain_community.document_loaders import UnstructuredEPubLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_weaviate.vectorstores import WeaviateVectorStore
from weaviate.classes.query import Filter

from src.infrastructure.memory.base_vector_store import BaseVectorStore
from src.infrastructure.memory.retry_decorator import retry_on_error

logger = logging.getLogger(__name__)


class BookContentStore(BaseVectorStore):
    """書籍コンテンツの処理とベクトル化に特化したストア."""

    def __init__(self) -> None:
        """書籍コンテンツストアの初期化."""
        super().__init__()

    @retry_on_error(max_retries=3)
    async def create_book_vector_index(self, file: UploadFile, user_id: str, book_id: str) -> dict:
        """EPUBファイルを処理してBookContentコレクションにベクトルインデックス化する."""
        try:
            # 一時ファイルとしてEPUBファイルを保存
            with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as temp_file:
                file_content = await file.read()
                temp_file.write(file_content)
                temp_path = temp_file.name

            try:
                # EPUBファイルを読み込み
                docs = UnstructuredEPubLoader(temp_path).load()

                # テキストを適切なサイズに分割
                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                split_docs = splitter.split_documents(docs)

                # 各ドキュメントにbook_idをメタデータとして追加
                for doc in split_docs:
                    doc.metadata["book_id"] = book_id

                # ログ出力
                logger.info(f"Creating book vector index with book_id: {book_id} for user: {user_id}")
                logger.info(f"Number of document chunks: {len(split_docs)}")
                if split_docs:
                    logger.info(f"Sample document metadata: {split_docs[0].metadata}")

                # ベクトルストアにドキュメントを保存
                WeaviateVectorStore.from_documents(
                    documents=split_docs,
                    embedding=self.embedding_model,
                    client=self.client,
                    index_name=self.BOOK_CONTENT_COLLECTION_NAME,
                    text_key="content",
                    tenant=user_id,
                    batch_size=64,
                )

                # 保存後の確認
                self._verify_saved_content(user_id, book_id)

                return {
                    "message": "Upload and processing completed successfully",
                    "file_name": file.filename,
                    "chunk_count": len(split_docs),
                    "index_name": self.BOOK_CONTENT_COLLECTION_NAME,
                    "user_id": user_id,
                    "book_id": book_id,
                    "success": True,
                }
            finally:
                # 一時ファイルを削除
                Path(temp_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"書籍ベクトル化エラー: {str(e)}")
            raise ValueError(f"Error occurred during vector indexing: {str(e)}")

    def _verify_saved_content(self, user_id: str, book_id: str) -> None:
        """保存されたコンテンツを確認."""
        try:
            collection = self.client.collections.get(self.BOOK_CONTENT_COLLECTION_NAME)
            test_results = collection.with_tenant(user_id).query.fetch_objects(
                filters=Filter.by_property("book_id").equal(book_id), limit=1, return_properties=["content", "book_id"]
            )

            if test_results.objects:
                logger.info(f"✓ Book content saved successfully with book_id: {book_id}")
                logger.info(f"  Sample properties: {test_results.objects[0].properties}")
            else:
                logger.warning(f"⚠ No content found with book_id: {book_id} after saving")
        except Exception as e:
            logger.error(f"Error verifying saved content: {str(e)}")

    @retry_on_error(max_retries=2)
    def delete_book_content(self, user_id: str, book_id: str) -> None:
        """書籍コンテンツをベクトルストアから削除."""
        try:
            collection = self.client.collections.get(self.BOOK_CONTENT_COLLECTION_NAME)
            collection_with_tenant = collection.with_tenant(user_id)
            collection_with_tenant.data.delete_many(where=Filter.by_property("book_id").equal(book_id))
            logger.info(f"Deleted book content from vector DB for book_id: {book_id}")
        except Exception as e:
            logger.error(f"Error deleting book content from vector DB: {str(e)}")
            raise
