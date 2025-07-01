from langchain_weaviate.vectorstores import WeaviateVectorStore

from src.infrastructure.memory.memory_vector_store import MemoryVectorStore


def get_book_content_vector_store() -> WeaviateVectorStore:
    """BookContent 用の VectorStore を取得する.

    MemoryVectorStore で生成済みの共有クライアント／Embedding を再利用し、
    不要なコネクションやモデルの重複ロードを防ぐ。
    """
    try:
        return WeaviateVectorStore(
            client=MemoryVectorStore.get_client(),
            text_key="content",
            index_name=MemoryVectorStore.BOOK_CONTENT_COLLECTION_NAME,
            embedding=MemoryVectorStore.get_embedding_model(),
        )
    except Exception:
        raise
