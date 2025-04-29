import weaviate
from langchain_openai import OpenAIEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore

from src.infrastructure.memory.memory_vector_store import MemoryVectorStore


def get_book_content_vector_store() -> WeaviateVectorStore:
    """特定のインデックス名に基づいてベクトルストアを取得します.
    インデックスが存在しない場合はNoneを返します.

    Args:
        index_name: Weaviateのインデックス名

    Returns:
        WeaviateVectorStoreインスタンス、または存在しない場合はNone

    """
    # インデックス（コレクション）が存在するか確認
    try:
        # 既存のインデックスに接続するWeaviateVectorStoreを作成
        return WeaviateVectorStore(
            client=weaviate.connect_to_local(),
            text_key="content",
            index_name=MemoryVectorStore.BOOK_CONTENT_COLLECTION_NAME,
            embedding=OpenAIEmbeddings(
                model="text-embedding-3-large",
                max_retries=2,
            ),
        )
    except Exception:
        raise
