"""Weaviateコレクション管理サービス."""

import logging

from weaviate.classes.config import Configure, DataType, Property

from src.infrastructure.memory.base_vector_store import BaseVectorStore
from src.infrastructure.memory.retry_decorator import retry_on_error

logger = logging.getLogger(__name__)


class CollectionManager(BaseVectorStore):
    """Weaviateコレクションの作成と管理を行うサービス."""

    def __init__(self) -> None:
        """コレクション管理サービスの初期化."""
        super().__init__()
        self._ensure_collections()

    @retry_on_error(max_retries=3, initial_delay=1)
    def _ensure_collections(self) -> None:
        """Weaviateコレクションが存在することを保証."""
        try:
            self._create_chat_memory_collection()
            self._create_book_content_collection()
            self._create_book_annotation_collection()
        except Exception as e:
            logger.error(f"コレクション作成エラー: {str(e)}")
            raise

    def _create_chat_memory_collection(self) -> None:
        """ChatMemoryコレクションを作成."""
        if not self.client.collections.exists(self.CHAT_MEMORY_COLLECTION_NAME):
            self.client.collections.create(
                name=self.CHAT_MEMORY_COLLECTION_NAME,
                multi_tenancy_config=Configure.multi_tenancy(
                    enabled=True,
                    auto_tenant_activation=True,
                    auto_tenant_creation=True,
                ),
                vectorizer_config=None,
                properties=[
                    Property(
                        name="chat_id",
                        data_type=DataType.TEXT,
                        description="チャットID",
                        index_searchable=True,
                    ),
                    Property(
                        name="content",
                        data_type=DataType.TEXT,
                        description="メッセージ/要約の内容",
                    ),
                    Property(
                        name="created_at",
                        data_type=DataType.DATE,
                        description="作成日時",
                    ),
                    Property(
                        name="is_summarized",
                        data_type=DataType.BOOL,
                        description="要約済みフラグ（メッセージ専用）",
                    ),
                    Property(
                        name="memory_type",
                        data_type=DataType.TEXT,
                        description="記憶の種類（message, summary）",
                        index_searchable=True,
                    ),
                    Property(
                        name="message_id",
                        data_type=DataType.TEXT,
                        description="元のメッセージID",
                    ),
                    Property(
                        name="sender",
                        data_type=DataType.TEXT,
                        description="送信者タイプ（user, assistant, system）",
                        index_searchable=True,
                    ),
                    Property(
                        name="user_id",
                        data_type=DataType.TEXT,
                        description="ユーザーID",
                        index_searchable=True,
                    ),
                ],
            )

    def _create_book_content_collection(self) -> None:
        """BookContentコレクションを作成."""
        if not self.client.collections.exists(self.BOOK_CONTENT_COLLECTION_NAME):
            self.client.collections.create(
                name=self.BOOK_CONTENT_COLLECTION_NAME,
                vectorizer_config=None,
                properties=[
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="book_id", data_type=DataType.TEXT, index_searchable=True, description="書籍ID"),
                ],
                multi_tenancy_config=Configure.multi_tenancy(
                    enabled=True,
                    auto_tenant_activation=True,
                    auto_tenant_creation=True,
                ),
            )

    def _create_book_annotation_collection(self) -> None:
        """BookAnnotationコレクションを作成."""
        if not self.client.collections.exists(self.BOOK_ANNOTATION_COLLECTION_NAME):
            self.client.collections.create(
                name=self.BOOK_ANNOTATION_COLLECTION_NAME,
                vectorizer_config=None,
                multi_tenancy_config=Configure.multi_tenancy(
                    enabled=True,
                    auto_tenant_activation=True,
                    auto_tenant_creation=True,
                ),
                properties=[
                    Property(
                        name="annotation_id",
                        data_type=DataType.TEXT,
                        description="アノテーションID",
                        index_searchable=True,
                    ),
                    Property(
                        name="book_id",
                        data_type=DataType.TEXT,
                        description="書籍ID",
                        index_searchable=True,
                    ),
                    Property(
                        name="book_title",
                        data_type=DataType.TEXT,
                        description="書籍タイトル",
                        index_searchable=True,
                    ),
                    Property(
                        name="content",
                        data_type=DataType.TEXT,
                        description="ハイライトされた本文",
                    ),
                    Property(
                        name="created_at",
                        data_type=DataType.DATE,
                        description="作成日時",
                    ),
                    Property(
                        name="notes",
                        data_type=DataType.TEXT,
                        description="メモ",
                    ),
                    Property(
                        name="user_id",
                        data_type=DataType.TEXT,
                        description="ユーザーID",
                        index_searchable=True,
                    ),
                ],
            )
