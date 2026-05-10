"""ChatManager._generate_chat_title の整形・フォールバック単体テスト.

- LLM 出力に「タイトル: ...」「"」などが混入したら除去される
- 空応答 / LLM 例外時にユーザー質問先頭からフォールバックされる
- 30 文字でカットされる
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

from unittest.mock import patch


def _fake_pipeline(returned_title: str | None):
    """`prompt | ChatOpenAI(...) | StrOutputParser()` を 1 つの fake で差し替える."""

    class _Result:
        def invoke(self, _: dict) -> str:
            if returned_title is None:
                raise RuntimeError("LLM unavailable")
            return returned_title

    return _Result()


def _build_chat_manager():
    from src.usecase.message.chat_manager import ChatManager

    # ChatRepository は使われないのでダミー
    class _DummyRepo:
        pass

    return ChatManager(_DummyRepo())  # type: ignore[arg-type]


def _patch_pipeline(returned_title: str | None):
    """`prompt | ChatOpenAI(...) | StrOutputParser()` の `__or__` チェーン全体を差し替える."""

    class _Chainable:
        def __init__(self, result: str | None) -> None:
            self._result = result

        def __or__(self, other):
            return self

        def __ror__(self, other):
            return self

        def invoke(self, _: dict) -> str:
            if self._result is None:
                raise RuntimeError("LLM unavailable")
            return self._result

    return _Chainable(returned_title)


def test_title_strip_quotes_and_prefix():
    cm = _build_chat_manager()
    chain = _patch_pipeline("「タイトル: 朝のルーティン」")
    with (
        patch("src.usecase.message.chat_manager.ChatPromptTemplate") as ptmpl,
        patch("src.usecase.message.chat_manager.ChatOpenAI"),
        patch("src.usecase.message.chat_manager.StrOutputParser"),
    ):
        ptmpl.from_messages.return_value = chain
        title = cm._generate_chat_title("朝のルーティンを教えて")
    assert "タイトル:" not in title
    assert "「" not in title
    assert "」" not in title
    assert len(title) <= 30


def test_title_fallback_on_empty_output():
    cm = _build_chat_manager()
    chain = _patch_pipeline("")
    with (
        patch("src.usecase.message.chat_manager.ChatPromptTemplate") as ptmpl,
        patch("src.usecase.message.chat_manager.ChatOpenAI"),
        patch("src.usecase.message.chat_manager.StrOutputParser"),
    ):
        ptmpl.from_messages.return_value = chain
        title = cm._generate_chat_title("これは質問本文の冒頭部分")
    assert title  # 空文字でない
    assert len(title) <= 30


def test_title_fallback_on_llm_exception():
    cm = _build_chat_manager()
    chain = _patch_pipeline(None)  # invoke で例外
    with (
        patch("src.usecase.message.chat_manager.ChatPromptTemplate") as ptmpl,
        patch("src.usecase.message.chat_manager.ChatOpenAI"),
        patch("src.usecase.message.chat_manager.StrOutputParser"),
    ):
        ptmpl.from_messages.return_value = chain
        title = cm._generate_chat_title("LLM 失敗のテスト")
    assert title


def test_title_fallback_when_question_is_empty():
    cm = _build_chat_manager()
    chain = _patch_pipeline(None)
    with (
        patch("src.usecase.message.chat_manager.ChatPromptTemplate") as ptmpl,
        patch("src.usecase.message.chat_manager.ChatOpenAI"),
        patch("src.usecase.message.chat_manager.StrOutputParser"),
    ):
        ptmpl.from_messages.return_value = chain
        title = cm._generate_chat_title("")
    assert title == "Untitled"
