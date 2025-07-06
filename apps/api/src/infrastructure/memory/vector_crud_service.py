"""ベクトルストアCRUD操作サービス."""

import logging

from weaviate.classes.query import Filter

from src.infrastructure.memory.base_vector_store import BaseVectorStore
from src.infrastructure.memory.retry_decorator import retry_on_error

logger = logging.getLogger(__name__)


class VectorCrudService(BaseVectorStore):
    """ベクトルストアの汎用CRUD操作を提供するサービス."""

    def __init__(self) -> None:
        """CRUD操作サービスの初期化."""
        super().__init__()

    @retry_on_error(max_retries=3)
    def add_memory(self, vector: list[float], metadata: dict, user_id: str, collection_name: str) -> str:
        """記憶を適切なベクトルストアコレクションに追加."""
        try:
            collection = self.client.collections.get(collection_name)
            inserted_id = collection.with_tenant(user_id).data.insert(properties=metadata, vector=vector)
            return str(inserted_id)
        except Exception as e:
            logger.error(f"{collection_name} へのメモリ追加エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def delete_memory(self, user_id: str, collection_name: str, target: str, key: str) -> None:
        """メモリを削除."""
        try:
            collection = self.client.collections.get(collection_name)
            collection_with_tenant = collection.with_tenant(user_id)

            collection_with_tenant.data.delete_many(where=Filter.by_property(target).equal(key))
            logger.info(f"Deleted memory from {collection_name} where {target}={key}")

        except Exception as e:
            logger.error(f"メモリ削除エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def update_memory(self, user_id: str, collection_name: str, target: str, key: str, properties: dict, vector: list[float]) -> None:
        """メモリを更新."""
        try:
            collection = self.client.collections.get(collection_name)
            collection_with_tenant = collection.with_tenant(user_id)

            # 対象のオブジェクトを検索
            response = collection_with_tenant.query.fetch_objects(filters=Filter.by_property(target).equal(key))

            if response.objects:
                uuid = response.objects[0].uuid
                collection_with_tenant.data.update(uuid=uuid, properties=properties, vector=vector)
                logger.info(f"Updated memory in {collection_name} where {target}={key}")
            else:
                logger.warning(f"Memory not found in {collection_name} where {target}={key}")

        except Exception as e:
            logger.error(f"メモリ更新エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def delete_book_data(self, user_id: str, book_id: str) -> None:
        """本に関連するすべてのベクターデータを削除.

        Args:
            user_id: ユーザーID
            book_id: 削除する本のID

        """
        try:
            # BookContentコレクションから削除
            self.delete_memory(user_id=user_id, collection_name=self.BOOK_CONTENT_COLLECTION_NAME, target="book_id", key=book_id)
            logger.info(f"Deleted book content from vector DB for book_id: {book_id}")
        except Exception as e:
            logger.error(f"Error deleting book content from vector DB: {str(e)}")
            # エラーが発生しても続行

        try:
            # BookAnnotationコレクションから削除
            self.delete_memory(user_id=user_id, collection_name=self.BOOK_ANNOTATION_COLLECTION_NAME, target="book_id", key=book_id)
            logger.info(f"Deleted book annotations from vector DB for book_id: {book_id}")
        except Exception as e:
            logger.error(f"Error deleting book annotations from vector DB: {str(e)}")
            # エラーが発生しても続行
