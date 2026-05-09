"""VectorCrudService の collection allow-list テスト.

M-6: 呼出元が任意の collection_name を指定できると、誤って別テナントの
コレクションに書き込みできてしまう。allow-list 検証を確認する。

Weaviate クライアントには接続せず、allow-list の判定だけを検証する。
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

import pytest

from src.infrastructure.memory.base_vector_store import BaseVectorStore
from src.infrastructure.memory.vector_crud_service import (
    _ALLOWED_COLLECTIONS,
    VectorCrudService,
)


def _build_service_without_init() -> VectorCrudService:
    """Weaviate 接続を回避するため __init__ をスキップしてインスタンスだけ作る."""
    service = VectorCrudService.__new__(VectorCrudService)
    # 必要な属性を mock で埋める
    service.client = MagicMock()
    service.embedding_model = MagicMock()
    return service


def test_allowed_collections_set():
    """ALLOW_LIST が定義済みの 3 コレクションを含む."""
    assert BaseVectorStore.CHAT_MEMORY_COLLECTION_NAME in _ALLOWED_COLLECTIONS
    assert BaseVectorStore.BOOK_CONTENT_COLLECTION_NAME in _ALLOWED_COLLECTIONS
    assert BaseVectorStore.BOOK_ANNOTATION_COLLECTION_NAME in _ALLOWED_COLLECTIONS


def test_insert_rejects_unknown_collection():
    service = _build_service_without_init()
    with pytest.raises(ValueError, match="Disallowed collection"):
        service._insert(vector=[0.0], metadata={}, user_id="u", collection_name="EvilCollection")


def test_delete_rejects_unknown_collection():
    service = _build_service_without_init()
    with pytest.raises(ValueError, match="Disallowed collection"):
        service._delete_by_property(
            user_id="u", collection_name="EvilCollection", target="id", key="x"
        )


def test_update_rejects_unknown_collection():
    service = _build_service_without_init()
    with pytest.raises(ValueError, match="Disallowed collection"):
        service._update_by_property(
            user_id="u",
            collection_name="EvilCollection",
            target="id",
            key="x",
            properties={},
            vector=[0.0],
        )


def test_named_methods_use_allowed_collection():
    """`add_chat_memory` 等は allow-list 内のコレクションを暗黙指定する."""
    service = _build_service_without_init()
    # client.collections.get が呼ばれることだけ確認する。
    # Real Weaviate connection なしで動くよう mock を返す。
    fake_collection = MagicMock()
    fake_collection.with_tenant.return_value.data.insert.return_value = "uuid-x"
    service.client.collections.get.return_value = fake_collection

    result = service.add_chat_memory(vector=[0.1], metadata={"k": "v"}, user_id="user-1")
    assert result == "uuid-x"
    service.client.collections.get.assert_called_with(BaseVectorStore.CHAT_MEMORY_COLLECTION_NAME)


def test_legacy_add_memory_validates_collection():
    """互換 API も allow-list 検証を経由する."""
    service = _build_service_without_init()
    with pytest.raises(ValueError, match="Disallowed collection"):
        service.add_memory(
            vector=[0.0], metadata={}, user_id="u", collection_name="UnknownCollection"
        )
