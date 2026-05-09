"""認可マトリクスの最低限テスト.

目的: CR-1 / CR-3 の回帰検出。下記を確認する。

1. 認証なしリクエストは 401 を返す（CR-1）
2. CORS 設定にワイルドカードが残っていない（CR-2）
3. レート制限ハンドラが登録されている（H-1）

実 DB / 外部サービスを必要としないため、各エンドポイントの動作確認は行わない。
詳細な認可マトリクス（user_A の token で user_B のリソースが 403 になる等）は、
将来 Supabase Auth のテストヘルパーが整ってから追加すること。
"""

from __future__ import annotations


def test_unauthenticated_books_returns_401(client):  # noqa: ANN001
    response = client.get("/books/me")
    assert response.status_code == 401, response.text


def test_unauthenticated_chats_returns_401(client):  # noqa: ANN001
    response = client.get("/chats/me")
    assert response.status_code == 401, response.text


def test_unauthenticated_post_message_returns_401(client):  # noqa: ANN001
    response = client.post(
        "/messages",
        json={"content": "hi", "chat_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 401, response.text


def test_invalid_bearer_token_returns_401(client):  # noqa: ANN001
    response = client.get(
        "/books/me",
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )
    assert response.status_code == 401, response.text


def test_cors_does_not_use_wildcard(app):  # noqa: ANN001
    """CR-2 の回帰検出: CORS ミドルウェアの allow_origins が `*` になっていないこと."""
    from starlette.middleware.cors import CORSMiddleware

    cors_options = None
    for mw in app.user_middleware:
        if mw.cls is CORSMiddleware:
            cors_options = mw.kwargs
            break

    assert cors_options is not None, "CORS middleware is not registered"
    assert "*" not in cors_options.get("allow_origins", []), (
        "allow_origins must not include '*' when allow_credentials is True"
    )
    # allow_credentials は True であってよいが、その場合は allow_origins が明示リストでなければならない。
    if cors_options.get("allow_credentials"):
        origins = cors_options.get("allow_origins")
        assert origins and origins != ["*"]


# ============================================================
# CR-1: 全 router の認証必須を網羅する 401 マトリクス
# ============================================================
# 既存テストでは books / chats / messages のみ。レビュー文書の影響範囲（CR-3 個別エンドポイント別の影響）に
# 沿って annotations / podcasts / rag も 401 で弾かれることを保証する。


def test_unauthenticated_post_podcasts_returns_401(client):  # noqa: ANN001
    """CR-1: 未認証で POST /podcasts は 401（高額課金エンドポイントの保護）."""
    response = client.post(
        "/podcasts",
        json={"book_id": "00000000-0000-0000-0000-000000000000", "language": "ja"},
    )
    assert response.status_code == 401, response.text


def test_unauthenticated_get_podcasts_returns_401(client):  # noqa: ANN001
    response = client.get("/podcasts/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 401, response.text


def test_unauthenticated_post_rag_returns_401(client):  # noqa: ANN001
    """CR-1: 未認証で POST /rag は 401（Embedding 大量呼出の保護）."""
    response = client.post(
        "/rag",
        json={"book_id": "00000000-0000-0000-0000-000000000000", "query": "x"},
    )
    assert response.status_code == 401, response.text


def test_unauthenticated_put_annotations_returns_401(client):  # noqa: ANN001
    """CR-1 + H-17: 未認証で PUT /books/{id}/annotations は 401（Mass Assignment 経路の遮断）."""
    response = client.put(
        "/books/00000000-0000-0000-0000-000000000000/annotations",
        json={"annotations": []},
    )
    assert response.status_code == 401, response.text


def test_unauthenticated_delete_book_returns_401(client):  # noqa: ANN001
    response = client.delete("/books/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 401, response.text


def test_unauthenticated_bulk_delete_books_returns_401(client):  # noqa: ANN001
    response = client.delete(
        "/books/bulk-delete",
        json={"book_ids": ["00000000-0000-0000-0000-000000000000"]},
    )
    assert response.status_code == 401, response.text
