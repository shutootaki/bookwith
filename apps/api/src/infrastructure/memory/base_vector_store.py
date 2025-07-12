"""ベクトルストア基底クラス."""

import logging

import weaviate
from langchain_openai import OpenAIEmbeddings
from weaviate.classes.init import AdditionalConfig, Timeout

from src.config.app_config import AppConfig
from src.infrastructure.memory.retry_decorator import retry_on_error

logger = logging.getLogger(__name__)


class BaseVectorStore:
    """ベクトルストアの基底クラス.

    Weaviateクライアントと埋め込みモデルの共有管理を行う。
    """

    # コレクション名の定数
    CHAT_MEMORY_COLLECTION_NAME = "ChatMemory"
    BOOK_CONTENT_COLLECTION_NAME = "BookContent"
    BOOK_ANNOTATION_COLLECTION_NAME = "BookAnnotation"

    # メモリタイプ定義
    TYPE_MESSAGE = "message"
    TYPE_SUMMARY = "summary"

    # 共有シングルトンインスタンス
    _shared_client: weaviate.WeaviateClient | None = None
    _shared_embedding_model: OpenAIEmbeddings | None = None

    def __init__(self) -> None:
        """基底ベクトルストアの初期化."""
        self.config = AppConfig.get_config()

        # Weaviate クライアントを共有インスタンスとして保持
        if BaseVectorStore._shared_client is None:
            BaseVectorStore._shared_client = self._create_client()

        self.client = BaseVectorStore._shared_client

        # Embedding モデルも共有インスタンスとして保持
        if BaseVectorStore._shared_embedding_model is None:
            BaseVectorStore._shared_embedding_model = OpenAIEmbeddings(model="text-embedding-3-small", max_retries=2)

        self.embedding_model = BaseVectorStore._shared_embedding_model

    @retry_on_error(max_retries=5, initial_delay=2)
    def _create_client(self) -> weaviate.WeaviateClient:
        """Weaviateクライアントを作成."""
        try:
            return weaviate.connect_to_local(additional_config=AdditionalConfig(timeout=Timeout(init=30, query=60, insert=120)))
        except Exception as e:
            logger.error(f"Weaviate接続エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def encode_text(self, text: str) -> list[float]:
        """テキストをベクトル化."""
        return self.embedding_model.embed_query(text)

    @classmethod
    def get_client(cls) -> weaviate.WeaviateClient:
        """共有の Weaviate クライアントを返す."""
        if cls._shared_client is None:
            # インスタンス化時に _shared_client が作成されるため
            cls()
        return cls._shared_client  # type: ignore[return-value]

    @classmethod
    def get_embedding_model(cls) -> OpenAIEmbeddings:
        """共有の Embedding モデルを返す."""
        if cls._shared_embedding_model is None:
            cls()
        return cls._shared_embedding_model  # type: ignore[return-value]
