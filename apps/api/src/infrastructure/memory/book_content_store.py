"""書籍コンテンツストア."""

import logging
import tempfile
from pathlib import Path
from typing import Any

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

    def _extract_chapter_structure(self, elements: list) -> list[dict[str, Any]]:
        """EPUB要素から章構造を抽出する."""
        chapter_titles: list[dict[str, Any]] = []
        for elem in elements:
            if elem.metadata.get("category") == "Title":
                chapter_titles.append({"title": elem.page_content.strip(), "index": len(chapter_titles)})
        return chapter_titles

    def _process_text_content(self, elements: list, chapter_titles: list[dict[str, Any]]) -> list:
        """テキスト要素を処理し、章情報を付与する."""
        text_content = []
        current_chapter = None
        for elem in elements:
            if elem.metadata.get("category") == "Title":
                # 新しい章の開始
                current_title = elem.page_content.strip()
                current_chapter = next((ch for ch in chapter_titles if ch["title"] == current_title), None)
            elif elem.metadata.get("category") == "NarrativeText":
                # テキストコンテンツに現在の章情報を付与
                elem.metadata["chapter_title"] = current_chapter["title"] if current_chapter else "序章"
                elem.metadata["chapter_index"] = current_chapter["index"] if current_chapter else 0
                text_content.append(elem)
        return text_content

    def _add_document_metadata(self, split_docs: list, book_id: str) -> None:
        """ドキュメントにメタデータを追加する."""
        total_chunks = len(split_docs)
        for idx, doc in enumerate(split_docs):
            doc.metadata["book_id"] = book_id
            doc.metadata["chunk_index"] = idx
            doc.metadata["total_chunks"] = total_chunks
            doc.metadata["position_percent"] = round((idx / total_chunks) * 100, 2)
            # 内容のプレビュー（最初の100文字）
            doc.metadata["content_preview"] = doc.page_content[:100]
            # 章情報がない場合のデフォルト値
            if "chapter_title" not in doc.metadata:
                doc.metadata["chapter_title"] = "不明"
                doc.metadata["chapter_index"] = -1

            # CFI情報のプレースホルダー（将来的にフロントエンドと連携して生成）
            doc.metadata["cfi"] = None  # 将来的にはここにCFIを格納
            doc.metadata["spine_index"] = None  # spine（章）のインデックス

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
                # EPUBファイルを読み込み（elementsモードで構造を保持）
                loader = UnstructuredEPubLoader(temp_path, mode="elements")
                elements = loader.load()

                # 章構造を抽出
                chapter_titles = self._extract_chapter_structure(elements)

                # テキスト要素を処理
                text_content = self._process_text_content(elements, chapter_titles)

                # テキストを適切なサイズに分割
                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                split_docs = splitter.split_documents(text_content)

                # ドキュメントにメタデータを追加
                self._add_document_metadata(split_docs, book_id)

                # ログ出力
                logger.info(f"Creating book vector index with book_id: {book_id} for user: {user_id}")
                logger.info(f"Number of document chunks: {len(split_docs)}")
                logger.info(f"Number of chapters found: {len(chapter_titles)}")
                if chapter_titles:
                    logger.info(f"Chapter titles: {[ch['title'] for ch in chapter_titles[:5]]}...")  # 最初の5章のみ表示
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
                filters=Filter.by_property("book_id").equal(book_id),
                limit=1,
                return_properties=["content", "book_id", "chunk_index", "position_percent", "content_preview", "chapter_title", "chapter_index"],
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
