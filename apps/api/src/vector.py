from typing import Any, Optional

from langchain_core.vectorstores import InMemoryVectorStore

# 共有ベクトルストアを保持する変数
shared_vector_store: Optional[InMemoryVectorStore] = None


def set_shared_vector_store(vector_store: Any) -> None:
    """共有ベクトルストアを設定します"""
    global shared_vector_store
    shared_vector_store = vector_store


def get_shared_vector_store() -> Optional[Any]:
    """共有ベクトルストアを取得します"""
    global shared_vector_store
    return shared_vector_store
