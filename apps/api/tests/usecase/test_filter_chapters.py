"""B-3: ExtractChaptersUseCase._filter_chapters の動作テスト.

レビュー文書 04_bugs.md の B-3:
> `max_chapter_length=10000` を**チャプター数**比較に使用、本来 `max_chapters=15` のはず

修正後は `max_chapters` で chapter 数の上限を正しく評価するべき。
このテストは将来のリファクタで再び `max_chapter_length` を使ってしまう事故を回帰検出する。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

from src.infrastructure.external.epub.epub_reader import Chapter
from src.usecase.podcast.extract_chapters_usecase import ExtractChaptersUseCase


def _make_chapters(count: int) -> list[Chapter]:
    return [Chapter(index=i, title=f"ch-{i}", content="x" * 100) for i in range(count)]


def test_filter_returns_input_when_count_within_limit() -> None:
    usecase = ExtractChaptersUseCase()
    usecase.max_chapters = 15

    chapters = _make_chapters(10)
    result = usecase._filter_chapters(chapters)

    assert result == chapters


def test_filter_caps_to_max_chapters() -> None:
    """B-3: 上限を超えたら max_chapters 件まで間引いて返す."""
    usecase = ExtractChaptersUseCase()
    usecase.max_chapters = 15

    chapters = _make_chapters(100)
    result = usecase._filter_chapters(chapters)

    assert len(result) == 15
    assert all(isinstance(c, Chapter) for c in result)
    # 最初と最後付近のサンプルが含まれていること（間引きの戦略）
    assert result[0].index == 0


def test_filter_uses_max_chapters_not_max_chapter_length() -> None:
    """回帰検出: 万が一 `max_chapter_length` (10000) を比較に使うと len(chapters) > 10000 で初めて
    間引きが発火する。10001 件渡してその挙動になっていないかをテストで弾く."""
    usecase = ExtractChaptersUseCase()
    usecase.max_chapters = 15
    # max_chapter_length は文字数制限なので chapter 数比較に使うのは誤り
    usecase.max_chapter_length = 10_000

    chapters = _make_chapters(20)  # max_chapters=15 < 20 < max_chapter_length=10000
    result = usecase._filter_chapters(chapters)

    assert len(result) == 15, (
        "max_chapters (15) で間引かれるべき。max_chapter_length (10000) を比較に使うと "
        "20 件すべてがそのまま返ってしまうリグレッション。"
    )


def test_filter_respects_custom_max_chapters() -> None:
    usecase = ExtractChaptersUseCase()
    usecase.max_chapters = 5

    chapters = _make_chapters(50)
    result = usecase._filter_chapters(chapters)

    assert len(result) == 5


def test_filter_handles_max_chapters_equal_to_input() -> None:
    """境界条件: max_chapters と入力 chapter 数がちょうど一致する場合は全件そのまま返す."""
    usecase = ExtractChaptersUseCase()
    usecase.max_chapters = 15

    chapters = _make_chapters(15)
    result = usecase._filter_chapters(chapters)

    assert result == chapters
