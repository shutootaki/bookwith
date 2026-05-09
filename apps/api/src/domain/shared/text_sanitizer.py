"""ドメイン層共通の入力サニタイザ.

`sanitize_plain_text`: Frontend が `dangerouslySetInnerHTML` などで再描画した場合の
XSS を緩和するため、保存前に HTML 構文と危険な制御文字を取り除く。

`safe_xml_block`: LLM プロンプトインジェクション対策。ユーザー由来テキストを
XML 風タグで囲み、本文の指示には従わないよう system 側と組み合わせて使う。
"""

from __future__ import annotations

import re
import unicodedata

# `<` `>` `&` のうち、attribute 終端や script 開始に使われがちな組合せをストリップする。
_SCRIPT_STYLE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_HTML_LIKE = re.compile(r"<[^>]*>", re.DOTALL)
_NULL_BYTES = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]")
_AMPERSAND_ENTITY = re.compile(r"&(#?[a-zA-Z0-9]+);")


def safe_xml_block(label: str, content: str, *, max_chars: int = 24_000) -> str:
    """ユーザー由来テキストを XML 風タグで囲み、内部の指示を中和する.

    タグ内の同名閉じタグは `</_label>` に書き換えて早期クローズを防ぐ。
    """
    if not content:
        return f"<{label}></{label}>"
    truncated = content[:max_chars]
    cleaned = truncated.replace(f"</{label}>", f"</_{label}>")
    return f"<{label}>{cleaned}</{label}>"


def sanitize_plain_text(value: str, *, max_length: int) -> str:
    if value is None:
        raise ValueError("value is required")
    if not isinstance(value, str):
        raise TypeError("value must be a string")

    # Unicode 正規化で見た目同型 ⇒ 同一表現に揃える。
    normalized = unicodedata.normalize("NFKC", value)

    without_tags = _HTML_LIKE.sub("", _SCRIPT_STYLE.sub("", normalized))

    # 制御文字を除去（改行とタブは許容）
    cleaned = _NULL_BYTES.sub("", without_tags)

    # `&xyz;` 形式のエンティティは平文 `&` に置換し、再解釈されないようにする。
    cleaned = _AMPERSAND_ENTITY.sub(lambda m: "&amp;" + m.group(1) + ";", cleaned)

    cleaned = cleaned.strip()

    if max_length is not None and len(cleaned) > max_length:
        raise ValueError(f"value exceeds {max_length} characters")

    return cleaned
