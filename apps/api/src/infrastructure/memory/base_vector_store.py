"""ベクトルストア基底クラス."""

import logging
import threading

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
    # B-6: lazy init をスレッド安全にするため lock を導入。
    _client_lock = threading.Lock()
    _embedding_lock = threading.Lock()

    def __init__(self) -> None:
        """基底ベクトルストアの初期化."""
        self.config = AppConfig.get_config()

        # double-checked locking で 2 重生成を防ぐ。
        if BaseVectorStore._shared_client is None:
            with BaseVectorStore._client_lock:
                if BaseVectorStore._shared_client is None:
                    BaseVectorStore._shared_client = self._create_client()
        self.client = BaseVectorStore._shared_client

        if BaseVectorStore._shared_embedding_model is None:
            with BaseVectorStore._embedding_lock:
                if BaseVectorStore._shared_embedding_model is None:
                    BaseVectorStore._shared_embedding_model = OpenAIEmbeddings(model="text-embedding-3-small", max_retries=2)
        self.embedding_model = BaseVectorStore._shared_embedding_model

    @retry_on_error(max_retries=5, initial_delay=2)
    def _create_client(self) -> weaviate.WeaviateClient:
        """Weaviateクライアントを作成.

        C-02: 環境変数で Weaviate URL / API キーが指定されていれば認証付きで接続する。
        ローカル開発ではこれまで通り `connect_to_local` を使う。
        """
        timeout_config = AdditionalConfig(timeout=Timeout(init=30, query=60, insert=120))
        try:
            if self.config.weaviate_url and self.config.weaviate_api_key:
                from weaviate.auth import AuthApiKey

                http_host = self.config.weaviate_url.replace("https://", "").replace("http://", "")
                grpc_host = self.config.weaviate_grpc_host or http_host
                http_secure = self.config.weaviate_url.startswith("https://")
                return weaviate.connect_to_custom(
                    http_host=http_host,
                    http_port=443 if http_secure else 80,
                    http_secure=http_secure,
                    grpc_host=grpc_host,
                    grpc_port=self.config.weaviate_grpc_port,
                    grpc_secure=http_secure,
                    auth_credentials=AuthApiKey(self.config.weaviate_api_key),
                    additional_config=timeout_config,
                )
            return weaviate.connect_to_local(additional_config=timeout_config)
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
            cls()
        return cls._shared_client  # type: ignore[return-value]

    @classmethod
    def get_embedding_model(cls) -> OpenAIEmbeddings:
        """共有の Embedding モデルを返す."""
        if cls._shared_embedding_model is None:
            cls()
        return cls._shared_embedding_model  # type: ignore[return-value]
