r"""EPUB ファイルの事前安全性チェック.

`ebooklib` / `UnstructuredEPubLoader` が内部で使う `lxml` には XXE / Billion-Laughs 等の
攻撃面が残るため、以下のような多層防御を呼出側で実施する:

1. ZIP として開けることを確認 (PK\x03\x04 マジックは中間層で確認)
2. エントリ数の上限
3. 展開後合計サイズの上限 (zip-bomb 対策)
4. ZIP slip (`..` / 絶対パス) を含むエントリ拒否
5. 顕著な XML 攻撃パターン (`<!ENTITY` / `<!DOCTYPE` の SYSTEM 参照) のヒューリスティック

完全な対策ではないが、ebooklib / unstructured の lxml 設定を変更できないため、
入口で限界をはめておく。実害が出るペイロードは多くがここで弾かれる。
"""

from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)


# 通常 EPUB は数百エントリ程度。1000 あれば十分余裕。
_MAX_ZIP_ENTRIES = 1000
# zip-bomb 対策。25MB の EPUB が展開後 200MB 超になることは通常想定しない。
_MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
# zip-bomb 圧縮率上限。実用 EPUB は 10x 程度に収まる。
_MAX_COMPRESSION_RATIO = 100

# DOCTYPE / ENTITY 経由の SSRF / XXE / Billion-Laughs を簡易検出。
_DANGEROUS_XML_PATTERNS = [
    re.compile(rb"<!ENTITY[^>]*\bSYSTEM\b", re.IGNORECASE),
    re.compile(rb"<!ENTITY[^>]*\bPUBLIC\b", re.IGNORECASE),
    re.compile(rb"<!DOCTYPE[^>]*\[", re.IGNORECASE),
]


class UnsafeEpubError(ValueError):
    """EPUB が安全性チェックに失敗したことを示す."""


def assert_epub_is_safe(epub_path: str | Path) -> None:
    """EPUB ファイルを ebooklib に渡す前に静的検査する.

    検査に失敗した場合は `UnsafeEpubError` を上げる。
    """
    path = Path(epub_path)
    try:
        with zipfile.ZipFile(path) as zf:
            infos = zf.infolist()
            if len(infos) > _MAX_ZIP_ENTRIES:
                raise UnsafeEpubError(f"EPUB has too many entries ({len(infos)})")

            total_uncompressed = 0
            total_compressed = 0
            for info in infos:
                # ZIP slip 対策: 絶対パスや `..` を含むエントリを拒否。
                normalized = info.filename.replace("\\", "/")
                if normalized.startswith("/") or any(part == ".." for part in normalized.split("/")):
                    raise UnsafeEpubError(f"Suspicious EPUB entry path: {info.filename!r}")

                total_uncompressed += info.file_size
                total_compressed += info.compress_size
                if total_uncompressed > _MAX_UNCOMPRESSED_BYTES:
                    raise UnsafeEpubError("EPUB uncompressed size exceeds limit")

            if total_compressed and total_uncompressed / max(total_compressed, 1) > _MAX_COMPRESSION_RATIO:
                raise UnsafeEpubError("EPUB compression ratio exceeds zip-bomb threshold")

            # 危険な XML パターンを軽く検査。container.xml / OPF / NCX を中心に。
            xml_targets = [info for info in infos if info.filename.lower().endswith((".opf", ".ncx", ".xml", ".xhtml", ".html"))]
            for info in xml_targets[:64]:
                try:
                    with zf.open(info) as fh:
                        head = fh.read(4096)
                except Exception:
                    continue
                for pattern in _DANGEROUS_XML_PATTERNS:
                    if pattern.search(head):
                        raise UnsafeEpubError(f"Suspicious XML construct detected in EPUB entry {info.filename!r}")
    except UnsafeEpubError:
        raise
    except zipfile.BadZipFile as e:
        raise UnsafeEpubError("EPUB is not a valid ZIP container") from e
    except Exception as e:  # pragma: no cover
        logger.warning("EPUB safety inspection failed: %s", e)
        raise UnsafeEpubError("EPUB safety inspection failed") from e
