"""ExtractChaptersUseCase の SSRF / プロトコル防御テスト.

H-3 / B-1: `_is_safe_remote_url` がプライベート IP / 不正スキーム / allow-list 外を
正しく弾くことを検証する。実 HTTP 通信は行わない（純粋な検証関数のテスト）。
"""

from __future__ import annotations

import asyncio
import os
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

from src.usecase.podcast import extract_chapters_usecase as ec


def _is_safe(url: str) -> bool:
    return asyncio.run(ec._is_safe_remote_url(url))


async def _async_false(_host: str) -> bool:
    return False


def test_blocks_unsupported_scheme():
    assert _is_safe("file:///etc/passwd") is False
    assert _is_safe("javascript:alert(1)") is False
    assert _is_safe("data:text/plain,hi") is False
    assert _is_safe("gopher://x") is False


def test_blocks_private_ip_addresses():
    # localhost
    with patch.object(ec, "_allowed_epub_hosts", return_value=["127.0.0.1"]):
        assert _is_safe("http://127.0.0.1/x.epub") is False
    # RFC1918 ranges
    with patch.object(ec, "_allowed_epub_hosts", return_value=["10.0.0.1"]):
        assert _is_safe("http://10.0.0.1/x.epub") is False
    # link-local (GCE/AWS metadata)
    with patch.object(ec, "_allowed_epub_hosts", return_value=["169.254.169.254"]):
        assert _is_safe("http://169.254.169.254/latest/meta-data/") is False


def test_blocks_when_allow_list_empty():
    with patch.object(ec, "_allowed_epub_hosts", return_value=[]):
        # allow-list が空なら public ホストでも拒否
        assert _is_safe("https://example.com/x.epub") is False


def test_allows_explicit_allowed_host():
    """ホストが allow-list に登録されており、IP が public なら許可."""
    with patch.object(ec, "_allowed_epub_hosts", return_value=["standardebooks.org"]):
        # 実際の DNS 解決はテストでは public なはずだが、念のため _is_private_address をモック
        with patch.object(ec, "_is_private_address", side_effect=_async_false):
            assert _is_safe("https://standardebooks.org/x.epub") is True


def test_blocks_host_not_in_allow_list():
    with patch.object(ec, "_allowed_epub_hosts", return_value=["standardebooks.org"]):
        with patch.object(ec, "_is_private_address", side_effect=_async_false):
            assert _is_safe("https://evil.example/x.epub") is False


def test_url_without_hostname_blocked():
    assert _is_safe("http://") is False
    assert _is_safe("not-a-url") is False


# ============================================================
# Addendum B-1: aiohttp の timeout / size / redirect 設定の回帰検出
# ============================================================
# 実 HTTP は飛ばさず、定数値と関数呼び出し時の引数のみ検証する。
# これらが弱体化された瞬間（timeout なし / size 上限なし / allow_redirects=True 等）に
# テストが失敗するため、リファクタによる退行を即時検出できる。


def test_fetch_timeout_is_bounded():
    """B-1: 接続/読み取りに無限待機させない."""
    timeout = ec._FETCH_TIMEOUT
    # connect / total が None でない（=無限待機ではない）こと
    assert timeout.connect is not None and timeout.connect > 0
    assert timeout.total is not None and timeout.total > 0
    # 攻撃時の滞留を最小化するため、5 分以下を期待する
    assert timeout.total <= 300


def test_fetch_max_bytes_is_capped():
    """B-1: サイズ上限なしで OOM になる経路を塞ぐ."""
    max_bytes = ec._fetch_max_bytes()
    assert max_bytes > 0
    # 上限が大きすぎないこと（書籍 1 冊で 100 MiB を超えない想定）
    assert max_bytes <= 100 * 1024 * 1024


def test_fetch_only_allows_http_https_schemes():
    """B-1: http/https 以外のスキームを禁止."""
    assert ec._ALLOWED_SCHEMES == {"http", "https"}


def test_download_calls_session_get_with_redirects_disabled(monkeypatch):
    """B-1: `_download_remote_epub` が `allow_redirects=False` を渡していること.

    aiohttp.ClientSession.get の引数を捕捉して `allow_redirects` を確認する。
    """
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    captured: dict = {}

    class _FakeResp:
        def __init__(self) -> None:
            self.headers = {"Content-Length": "10"}
            self.content = MagicMock()
            # iter_chunked は async generator を返す
            async def _gen(_size):  # noqa: ANN001
                yield b"x" * 10
            self.content.iter_chunked = _gen

        def raise_for_status(self) -> None:
            return None

        async def __aenter__(self):  # noqa: ANN204
            return self

        async def __aexit__(self, *a, **kw):  # noqa: ANN001, ANN002, ANN003
            return False

    class _FakeSession:
        def __init__(self, *a, **kw):  # noqa: ANN001, ANN002, ANN003
            pass

        async def __aenter__(self):  # noqa: ANN204
            return self

        async def __aexit__(self, *a, **kw):  # noqa: ANN001, ANN002, ANN003
            return False

        def get(self, url, **kwargs):  # noqa: ANN001, ANN003
            captured["url"] = url
            captured["kwargs"] = kwargs
            return _FakeResp()

    # _is_safe_remote_url を素通しさせる (現在は async なので awaitable を返す)
    async def _always_safe(_url: str) -> bool:
        return True
    monkeypatch.setattr(ec, "_is_safe_remote_url", _always_safe)
    monkeypatch.setattr(ec.aiohttp, "ClientSession", _FakeSession)

    asyncio.run(ec._download_remote_epub("https://allowed.example/book.epub"))

    assert captured["kwargs"].get("allow_redirects") is False, (
        "_download_remote_epub must pass allow_redirects=False to prevent "
        "metadata-endpoint redirects"
    )
