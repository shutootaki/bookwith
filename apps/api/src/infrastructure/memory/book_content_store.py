"""書籍コンテンツストア."""

import logging
import os
import tempfile
from pathlib import Path

from fastapi import UploadFile
from langchain_community.document_loaders import UnstructuredEPubLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_weaviate.vectorstores import WeaviateVectorStore
from weaviate.classes.query import Filter

from src.config.app_config import AppConfig
from src.infrastructure.external.epub import assert_epub_is_safe
from src.infrastructure.memory.base_vector_store import BaseVectorStore
from src.infrastructure.memory.retry_decorator import retry_on_error

logger = logging.getLogger(__name__)


class BookContentStore(BaseVectorStore):
    """書籍コンテンツの処理とベクトル化に特化したストア."""

    def __init__(self) -> None:
        """書籍コンテンツストアの初期化."""
        super().__init__()

    # H-09: EPUB 全体の Embedding 計算は OpenAI 課金が走る非冪等処理。
    # 部分失敗で全 batch 再実行すると重複登録 + 二重課金の温床になるため retry しない。
    @retry_on_error(max_retries=0, idempotent=False)
    async def create_book_vector_index(self, file: UploadFile, user_id: str, book_id: str) -> dict:
        """EPUBファイルを処理してBookContentコレクションにベクトルインデックス化する."""
        config = AppConfig.get_config()
        try:
            file_content = await file.read()
            if len(file_content) > config.max_upload_bytes:
                raise ValueError("EPUB file too large")

            # `mkstemp` で fd を直接取得することで、ファイル生成と書き込みのあいだに
            # 第三者プロセスが掴み込む TOCTOU を防ぐ。
            fd, temp_path = tempfile.mkstemp(suffix=".epub")
            try:
                with os.fdopen(fd, "wb") as tmp:
                    tmp.write(file_content)

                # ZIP 構造と XML ヒューリスティックで静的検査。
                # ebooklib / unstructured が内部の lxml ハードニング設定を露出しないので、
                # 攻撃面を入口で削減する目的の多層防御。
                assert_epub_is_safe(temp_path)

                # EPUBファイルを読み込み
                docs = UnstructuredEPubLoader(temp_path).load()

                # テキストを適切なサイズに分割
                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                split_docs = splitter.split_documents(docs)

                # 各ドキュメントにbook_idをメタデータとして追加
                for doc in split_docs:
                    doc.metadata["book_id"] = book_id

                # 著作権物の本文や PII をログに残さないよう、件数 / ID のみ INFO で出す。
                logger.info("Creating book vector index for book_id=%s user=%s chunks=%d", book_id, user_id, len(split_docs))

                # バッチ処理でベクトルストアにドキュメントを保存
                BATCH_SIZE = 100  # バッチサイズを定義  # noqa: N806
                total_docs = len(split_docs)

                for i in range(0, total_docs, BATCH_SIZE):
                    batch_docs = split_docs[i : i + BATCH_SIZE]
                    logger.info(f"Processing batch {i // BATCH_SIZE + 1}/{(total_docs + BATCH_SIZE - 1) // BATCH_SIZE}")

                    # ベクトルストアにバッチを保存
                    WeaviateVectorStore.from_documents(
                        documents=batch_docs,
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
                logger.info("Book content saved successfully for book_id=%s", book_id)
            else:
                logger.warning("No content found with book_id=%s after saving", book_id)
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
