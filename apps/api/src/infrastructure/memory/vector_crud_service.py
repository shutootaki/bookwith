"""ベクトルストアCRUD操作サービス."""

import logging

from weaviate.classes.query import Filter

from src.infrastructure.memory.base_vector_store import BaseVectorStore
from src.infrastructure.memory.retry_decorator import retry_on_error

logger = logging.getLogger(__name__)


# M-6: 呼出元から `collection_name` を自由に指定できる API は、誤って別テナントの
# コレクションへ書き込み・削除する事故の窓口になる。専用メソッド経由に統一する。
_CHAT_MEMORY = BaseVectorStore.CHAT_MEMORY_COLLECTION_NAME
_BOOK_CONTENT = BaseVectorStore.BOOK_CONTENT_COLLECTION_NAME
_BOOK_ANNOTATION = BaseVectorStore.BOOK_ANNOTATION_COLLECTION_NAME

_ALLOWED_COLLECTIONS: frozenset[str] = frozenset({_CHAT_MEMORY, _BOOK_CONTENT, _BOOK_ANNOTATION})


def _assert_collection_allowed(collection_name: str) -> None:
    if collection_name not in _ALLOWED_COLLECTIONS:
        raise ValueError(f"Disallowed collection: {collection_name}")


class VectorCrudService(BaseVectorStore):
    """ベクトルストアの汎用CRUD操作を提供するサービス."""

    def __init__(self) -> None:
        """CRUD操作サービスの初期化."""
        super().__init__()

    # ------------------------------------------------------------------
    # 内部ヘルパー（外部公開しない）
    # ------------------------------------------------------------------

    @retry_on_error(max_retries=3)
    def _insert(self, vector: list[float], metadata: dict, user_id: str, collection_name: str) -> str:
        _assert_collection_allowed(collection_name)
        try:
            collection = self.client.collections.get(collection_name)
            inserted_id = collection.with_tenant(user_id).data.insert(properties=metadata, vector=vector)
            return str(inserted_id)
        except Exception:
            logger.exception("%s へのメモリ追加エラー", collection_name)
            raise

    @retry_on_error(max_retries=2)
    def _delete_by_property(self, user_id: str, collection_name: str, target: str, key: str) -> None:
        _assert_collection_allowed(collection_name)
        try:
            collection = self.client.collections.get(collection_name)
            collection_with_tenant = collection.with_tenant(user_id)
            collection_with_tenant.data.delete_many(where=Filter.by_property(target).equal(key))
            logger.info(f"Deleted memory from {collection_name} where {target}={key}")
        except Exception:
            logger.exception("メモリ削除エラー")
            raise

    @retry_on_error(max_retries=2)
    def _update_by_property(self, user_id: str, collection_name: str, target: str, key: str, properties: dict, vector: list[float]) -> None:
        _assert_collection_allowed(collection_name)
        try:
            collection = self.client.collections.get(collection_name)
            collection_with_tenant = collection.with_tenant(user_id)

            response = collection_with_tenant.query.fetch_objects(filters=Filter.by_property(target).equal(key))
            if response.objects:
                uuid = response.objects[0].uuid
                collection_with_tenant.data.update(uuid=uuid, properties=properties, vector=vector)
                logger.info(f"Updated memory in {collection_name} where {target}={key}")
            else:
                logger.warning(f"Memory not found in {collection_name} where {target}={key}")
        except Exception:
            logger.exception("メモリ更新エラー")
            raise

    # ------------------------------------------------------------------
    # 名前付き専用メソッド（外部はこちらだけ使う）
    # ------------------------------------------------------------------

    def add_chat_memory(self, vector: list[float], metadata: dict, user_id: str) -> str:
        return self._insert(vector=vector, metadata=metadata, user_id=user_id, collection_name=_CHAT_MEMORY)

    def add_book_content(self, vector: list[float], metadata: dict, user_id: str) -> str:
        return self._insert(vector=vector, metadata=metadata, user_id=user_id, collection_name=_BOOK_CONTENT)

    def add_book_annotation(self, vector: list[float], metadata: dict, user_id: str) -> str:
        return self._insert(vector=vector, metadata=metadata, user_id=user_id, collection_name=_BOOK_ANNOTATION)

    def update_chat_memory(self, user_id: str, target: str, key: str, properties: dict, vector: list[float]) -> None:
        self._update_by_property(user_id=user_id, collection_name=_CHAT_MEMORY, target=target, key=key, properties=properties, vector=vector)

    def update_book_annotation(self, user_id: str, target: str, key: str, properties: dict, vector: list[float]) -> None:
        self._update_by_property(user_id=user_id, collection_name=_BOOK_ANNOTATION, target=target, key=key, properties=properties, vector=vector)

    def delete_chat_memory(self, user_id: str, target: str, key: str) -> None:
        self._delete_by_property(user_id=user_id, collection_name=_CHAT_MEMORY, target=target, key=key)

    def delete_book_annotation_memory(self, user_id: str, annotation_id: str) -> None:
        self._delete_by_property(user_id=user_id, collection_name=_BOOK_ANNOTATION, target="annotation_id", key=annotation_id)

    @retry_on_error(max_retries=2)
    def delete_book_data(self, user_id: str, book_id: str) -> None:
        """本に紐づく全ベクターデータ（content + annotations）を削除する."""
        for collection in (_BOOK_CONTENT, _BOOK_ANNOTATION):
            try:
                self._delete_by_property(user_id=user_id, collection_name=collection, target="book_id", key=book_id)
                logger.info(f"Deleted from {collection} for book_id: {book_id}")
            except Exception:
                logger.exception("Error deleting from %s for book_id %s", collection, book_id)

    # ------------------------------------------------------------------
    # 後方互換（既存呼び出し向けエイリアス）
    # ------------------------------------------------------------------

    def add_memory(self, vector: list[float], metadata: dict, user_id: str, collection_name: str) -> str:
        """旧 API。`collection_name` は allow-list に含まれる場合のみ通す。"""
        return self._insert(vector=vector, metadata=metadata, user_id=user_id, collection_name=collection_name)

    def delete_memory(self, user_id: str, collection_name: str, target: str, key: str) -> None:
        """旧 API。allow-list 検証を経由する."""
        self._delete_by_property(user_id=user_id, collection_name=collection_name, target=target, key=key)

    def update_memory(self, user_id: str, collection_name: str, target: str, key: str, properties: dict, vector: list[float]) -> None:
        """旧 API。allow-list 検証を経由する."""
        self._update_by_property(user_id=user_id, collection_name=collection_name, target=target, key=key, properties=properties, vector=vector)
