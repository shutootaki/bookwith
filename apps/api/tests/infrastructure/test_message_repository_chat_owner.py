"""H-16: find_by_chat_id_for_user / find_latest_by_chat_id_for_user の認可検証.

これらのメソッドは MessageProcessor の `get_latest_messages` 経路で使われ、
他人の chat_id を指定された場合でも別ユーザーのメッセージを返してはいけない。

実 DB を立てる代わりに SQLAlchemy session を MagicMock 化し、生成されるクエリの
文字列表現に `chat.user_id` 結合と WHERE 句が含まれることを検証する。
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

from src.infrastructure.postgres.message.message_repository import MessageRepositoryImpl


class _FakeQuery:
    """SQLAlchemy `Query` の最小限フェイク. 実行時のメソッドチェーンを再現する."""

    def __init__(self) -> None:
        self.joined: list[object] = []
        self.filters: list[object] = []
        self.ordered: list[object] = []
        self._limit: int | None = None

    def join(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        self.joined.append((args, kwargs))
        return self

    def filter(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        self.filters.append((args, kwargs))
        return self

    def order_by(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        self.ordered.append((args, kwargs))
        return self

    def limit(self, value):  # noqa: ANN001
        self._limit = value
        return self

    def all(self) -> list[object]:
        return []


def _make_session() -> tuple[MagicMock, _FakeQuery]:
    fake_query = _FakeQuery()
    session = MagicMock()
    session.query.return_value = fake_query
    return session, fake_query


def test_find_by_chat_id_for_user_joins_chat_table_to_enforce_owner() -> None:
    session, fake_query = _make_session()
    repo = MessageRepositoryImpl(session)

    repo.find_by_chat_id_for_user(chat_id="some-chat", user_id="owner-uuid")

    # 1) ChatDTO を join していること
    joined_repr = repr(fake_query.joined)
    assert "Chat" in joined_repr or "chats" in joined_repr, (
        f"Expected join with ChatDTO, got: {joined_repr}"
    )
    # 2) WHERE 句に chat の user_id 制約が出ていること
    filter_repr = repr(fake_query.filters)
    assert "user_id" in filter_repr, (
        f"Expected user_id in filter, got: {filter_repr}"
    )


def test_find_latest_by_chat_id_for_user_applies_limit_and_owner_filter() -> None:
    session, fake_query = _make_session()
    repo = MessageRepositoryImpl(session)

    repo.find_latest_by_chat_id_for_user(chat_id="some-chat", limit=5, user_id="owner-uuid")

    assert fake_query._limit == 5
    joined_repr = repr(fake_query.joined)
    assert "Chat" in joined_repr or "chats" in joined_repr
    filter_repr = repr(fake_query.filters)
    assert "user_id" in filter_repr


def test_find_by_chat_id_legacy_is_kept_but_unsafe_for_external_callers() -> None:
    """legacy `find_by_chat_id` (owner-aware でない方) は内部用途専用なので、
    本テストでは「user_id フィルタが付いていない」ことを明示的に検証して
    将来的な誤用を可視化する."""
    session, fake_query = _make_session()
    repo = MessageRepositoryImpl(session)

    repo.find_by_chat_id(chat_id="some-chat")

    filter_repr = repr(fake_query.filters)
    # legacy 経路は ownership を持たない（=これを公開エンドポイントに直結すると IDOR になる）
    assert "user_id" not in filter_repr, (
        "legacy find_by_chat_id must not silently grow ownership filter; "
        "use find_by_chat_id_for_user for any user-facing call"
    )
