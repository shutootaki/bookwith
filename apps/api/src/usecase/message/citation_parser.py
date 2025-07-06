"""引用情報パーサー."""

import logging
import re
from typing import Optional, TypedDict

logger = logging.getLogger(__name__)


class CitationData(TypedDict):
    """引用データの型定義."""

    marker: str
    number: str
    chapter: str
    position_percent: Optional[float]
    cfi: Optional[str]
    location_info: Optional[str]
    is_highlight: Optional[bool]


class CitationResult(TypedDict):
    """引用抽出結果の型定義."""

    citations: list[CitationData]
    has_citations: bool
    markers_found: list[str]


class CitationParser:
    """AIレスポンスから引用情報を抽出するパーサー."""

    # 上付き数字のマッピング
    SUPERSCRIPT_MAP = {
        "¹": "1",
        "²": "2",
        "³": "3",
        "⁴": "4",
        "⁵": "5",
        "⁶": "6",
        "⁷": "7",
        "⁸": "8",
        "⁹": "9",
    }

    # 逆マッピング（数字から上付き文字へ）
    REVERSE_SUPERSCRIPT_MAP = {v: k for k, v in SUPERSCRIPT_MAP.items()}

    @classmethod
    def extract_citations(cls, text: str) -> CitationResult:
        """テキストから引用情報を抽出する.

        Args:
            text: AIレスポンステキスト

        Returns:
            引用情報を含む辞書

        """
        citations = []

        # 本文中の上付き数字を検出
        superscript_pattern = r"[¹²³⁴⁵⁶⁷⁸⁹]"
        markers_in_text = re.findall(superscript_pattern, text)

        # 「参照箇所：」セクションを探す
        reference_section_match = re.search(r"参照箇所[：:]\s*\n((?:.*\n?)*)", text, re.MULTILINE)

        if reference_section_match:
            reference_section = reference_section_match.group(1)

            # 各参照行をパース
            # パターン: ¹ 第3章: タイトル（約25%の位置）
            reference_pattern = r"([¹²³⁴⁵⁶⁷⁸⁹])\s+([^（]+)（約(\d+(?:\.\d+)?)%の位置）"

            for match in re.finditer(reference_pattern, reference_section):
                marker = match.group(1)
                chapter_info = match.group(2).strip()
                
                try:
                    position_percent = float(match.group(3))
                except ValueError:
                    logger.warning(f"Invalid position percent: {match.group(3)}")
                    position_percent = 0.0

                citations.append(
                    CitationData(
                        marker=marker,
                        number=cls.SUPERSCRIPT_MAP.get(marker, "?"),
                        chapter=chapter_info,
                        position_percent=position_percent,
                        cfi=None,  # 将来的にCFI情報を追加
                        location_info=None,
                        is_highlight=None,
                    )
                )

        # ハイライト引用も検出（★マーカー）
        highlight_pattern = r"(★\d+)\s+([^（]+)（([^）]+)）"

        for match in re.finditer(highlight_pattern, text):
            marker = match.group(1)
            chapter_info = match.group(2).strip()
            location_info = match.group(3)

            # ハイライトの場合は位置情報が異なる可能性がある
            citations.append(
                CitationData(
                    marker=marker,
                    number=marker[1:],  # ★を除いた数字
                    chapter=chapter_info,
                    position_percent=None,  # ハイライトの場合は位置％がないかも
                    location_info=location_info,
                    is_highlight=True,
                    cfi=None,
                )
            )

        return CitationResult(
            citations=citations,
            has_citations=len(citations) > 0,
            markers_found=list(set(markers_in_text)),
        )

    @classmethod
    def add_citation_links(cls, text: str, citations: list[CitationData]) -> str:
        """テキスト内の引用マーカーをリンク可能な形式に変換する.

        フロントエンドで処理しやすいように、マーカーを特殊なタグで囲む。

        Args:
            text: 元のテキスト
            citations: 引用情報のリスト

        Returns:
            マーカーがタグで囲まれたテキスト

        """
        result = text

        # 引用マーカーをタグで囲む
        for citation in citations:
            marker = citation["marker"]
            # 例: ¹ → <citation-link marker="¹" index="0">¹</citation-link>
            # フロントエンドでこのタグを検出してリンクに変換する
            replacement = f'<citation-link marker="{marker}" number="{citation["number"]}">{marker}</citation-link>'
            result = result.replace(marker, replacement)

        return result
