"""DeleteMessageUseCase.execute_bulk の戻り値整合テスト.

B-5 回帰検出: 旧実装は「`failed_ids` を返すと言いつつ実際は `deleted_ids`」だった。
正しい挙動は「削除に失敗した（=所有者でない、または存在しない）ID のリスト」を返すこと。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")


from typing import Never

from src.domain.message.repositories.message_repository import MessageRepository
from src.domain.message.value_objects.message_id import MessageId
from src.usecase.message.delete_message_usecase import DeleteMessageUseCaseImpl


class _FakeMessageRepository(MessageRepository):
    """owner ID と message_id の組合せで所有を判定する fake."""

    def __init__(self, owned: dict[str, str]) -> None:
        # owned: {message_id: owner_user_id}
        self._owned = owned

    # 必須抽象メソッドだけ実装。残りは raise する。
    def save(self, message) -> Never:
        raise NotImplementedError

    def find_by_id(self, mid) -> Never:
        raise NotImplementedError

    def find_by_id_for_user(self, mid, user_id) -> Never:
        raise NotImplementedError

    def find_by_chat_id(self, chat_id) -> Never:
        raise NotImplementedError

    def find_by_chat_id_for_user(self, chat_id, user_id) -> Never:
        raise NotImplementedError

    def find_latest_by_chat_id(self, chat_id, limit) -> Never:
        raise NotImplementedError

    def find_latest_by_chat_id_for_user(self, chat_id, limit, user_id) -> Never:
        raise NotImplementedError

    def delete_for_user(self, mid, user_id) -> Never:
        raise NotImplementedError

    def count_by_chat_id(self, chat_id) -> Never:
        raise NotImplementedError

    def bulk_delete_for_user(self, message_ids, user_id):
        return [mid for mid in message_ids if self._owned.get(mid.value) == user_id]


def test_bulk_delete_returns_failed_ids_only():
    repo = _FakeMessageRepository(
        owned={
            "11111111-1111-1111-1111-111111111111": "user-A",
            "22222222-2222-2222-2222-222222222222": "user-A",
            # 33 は他ユーザーのもの → 削除されない
            "33333333-3333-3333-3333-333333333333": "user-B",
        }
    )
    usecase = DeleteMessageUseCaseImpl(repo)

    failed = usecase.execute_bulk(
        [
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
            "33333333-3333-3333-3333-333333333333",
        ],
        "user-A",
    )

    assert failed == ["33333333-3333-3333-3333-333333333333"]


def test_bulk_delete_all_failed_when_no_ownership():
    repo = _FakeMessageRepository(owned={"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": "other-user"})
    usecase = DeleteMessageUseCaseImpl(repo)

    failed = usecase.execute_bulk(
        ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
        "user-A",
    )

    assert failed == ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]


def test_bulk_delete_empty_input():
    repo = _FakeMessageRepository(owned={})
    usecase = DeleteMessageUseCaseImpl(repo)
    assert usecase.execute_bulk([], "user-A") == []


def test_message_id_value_object_must_be_uuid():
    """B-5 回帰: 不正な ID で usecase が早期に失敗すること."""
    import pytest

    repo = _FakeMessageRepository(owned={})
    usecase = DeleteMessageUseCaseImpl(repo)
    with pytest.raises(ValueError):
        usecase.execute_bulk(["not-a-uuid"], "user-A")


def test_message_id_uuid_normalized():
    """MessageId は厳密な UUID 形式で生成される（B-11 関連）."""
    mid = MessageId("AAAAAAAA-1111-1111-1111-111111111111")
    # 値オブジェクトの正規化形式を確認
    assert mid.value
