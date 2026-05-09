import asyncio
import ipaddress
import logging
import os
import socket
import tempfile
from urllib.parse import urlparse

import aiohttp
from ebooklib import ITEM_DOCUMENT, epub

from src.config.app_config import AppConfig
from src.infrastructure.external.epub import Chapter, assert_epub_is_safe

logger = logging.getLogger(__name__)


# H-3 / B-1: 外部 HTTP fetch のサイズ・タイムアウト・スキーム・ホスト制約を全て明示する。
_FETCH_TIMEOUT = aiohttp.ClientTimeout(total=30, connect=10)
_ALLOWED_SCHEMES = {"http", "https"}


def _fetch_max_bytes() -> int:
    """remote fetch のサイズ上限。ローカルアップロードと同じ `max_upload_bytes` に揃え、
    アップロード経路と remote 経路で受入サイズが乖離するのを防ぐ。"""
    return AppConfig.get_config().max_upload_bytes


async def _is_private_address(host: str) -> bool:
    """ループバック / リンクローカル / プライベート / メタデータエンドポイントを拒否する.

    DNS 解決が同期 socket だと event loop を秒単位で塞ぐため、loop.getaddrinfo を使う。
    """
    loop = asyncio.get_running_loop()
    try:
        addrinfos = await loop.getaddrinfo(host, None)
    except socket.gaierror:
        # 解決失敗は「危険なホスト」として扱う。
        return True

    for ai in addrinfos:
        addr = ai[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return True
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return True
    return False


def _allowed_epub_hosts() -> list[str]:
    """外部 EPUB fetch を許可するホスト名のリスト. 空なら全拒否。"""
    return AppConfig.get_config().epub_fetch_allowed_hosts_list


async def _is_safe_remote_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return False
    if not parsed.hostname:
        return False

    # H-3: allow-list が空なら外部 fetch を全拒否。GCS 直接アクセスは GCS SDK 経由を推奨。
    allowed = _allowed_epub_hosts()
    if not allowed:
        return False
    if parsed.hostname not in allowed:
        return False
    if await _is_private_address(parsed.hostname):
        return False
    return True


async def _download_remote_epub(url: str) -> bytes:
    """SSRF / DoS 対策付きで EPUB を取得する."""
    if not await _is_safe_remote_url(url):
        raise ValueError("Refusing to fetch untrusted URL")

    max_bytes = _fetch_max_bytes()
    async with aiohttp.ClientSession(timeout=_FETCH_TIMEOUT) as session:
        async with session.get(url, allow_redirects=False) as resp:
            resp.raise_for_status()

            # Content-Length 事前チェック。
            content_length = resp.headers.get("Content-Length")
            if content_length and int(content_length) > max_bytes:
                raise ValueError("Remote EPUB exceeds size limit")

            buffer = bytearray()
            async for chunk in resp.content.iter_chunked(64 * 1024):
                buffer.extend(chunk)
                if len(buffer) > max_bytes:
                    raise ValueError("Remote EPUB exceeds size limit")
            return bytes(buffer)


class ExtractChaptersUseCase:
    """Use case for extracting and processing chapters from EPUB files"""

    def __init__(self) -> None:
        # B-3: max_chapter_length は文字数制限。chapter 数の上限は max_chapters とは別概念。
        self.max_chapter_length = 10_000
        self.max_chapters = AppConfig.get_config().max_chapters

    async def execute(self, epub_path: str) -> list[Chapter]:
        """Extract and process chapters from an EPUB file."""
        logger.info(f"Extracting chapters from {epub_path}")

        chapters = await self._extract_chapters(epub_path)

        # B-3: chapter 数の上限と長さ分割をそれぞれ適用する。
        filtered_chapters = self._filter_chapters(chapters)
        processed_chapters = self._split_long_chapters(filtered_chapters)

        logger.info(f"Processed {len(processed_chapters)} chapters (original: {len(chapters)})")

        return processed_chapters

    async def _extract_chapters(self, epub_path: str) -> list[Chapter]:
        """Extract chapters from an EPUB file."""
        try:
            if epub_path.startswith(("http://", "https://")):
                try:
                    data = await _download_remote_epub(epub_path)

                    # mkstemp で fd を直接受け取り、生成と書き込みのあいだに第三者が
                    # 掴むのを防ぐ (TOCTOU 緩和)。
                    fd, tmp_path = tempfile.mkstemp(suffix=".epub")
                    try:
                        with os.fdopen(fd, "wb") as tmp_file:
                            tmp_file.write(data)
                        # ebooklib は内部の lxml ハードニングを露出しないため、
                        # 受け入れ前に ZIP / XML 構造を静的検査する。
                        assert_epub_is_safe(tmp_path)
                        book = epub.read_epub(tmp_path)
                    finally:
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            logger.warning(
                                "Failed to remove temporary EPUB file %s after processing.",
                                tmp_path,
                            )
                except Exception as url_err:
                    logger.error(f"Failed to download EPUB from URL {epub_path}: {url_err}")
                    raise
            else:
                # ローカルパスは GCS 由来のみ想定。`file://` 等のスキームは許可しない。
                if epub_path.startswith("file://"):
                    raise ValueError("file:// scheme is not allowed")
                assert_epub_is_safe(epub_path)
                book = epub.read_epub(epub_path)
            chapters = []

            for item in book.get_items_of_type(ITEM_DOCUMENT):
                content = item.get_content().decode("utf-8", errors="ignore")

                if len(content) < 100:
                    continue

                title = item.get_name()
                if hasattr(item, "title") and item.title:
                    title = item.title

                chapter = Chapter(index=len(chapters), title=title, content=content)

                if len(chapter.text_content) > 50:
                    chapters.append(chapter)

            if not chapters:
                raise ValueError("No chapters found in EPUB file")

            logger.info(f"Extracted {len(chapters)} chapters from EPUB")
            return chapters

        except Exception as e:
            logger.error(f"Error extracting chapters from EPUB: {str(e)}")
            raise

    def _split_long_chapters(self, chapters: list[Chapter]) -> list[Chapter]:
        processed_chapters = []

        for chapter in chapters:
            text = chapter.get_text_content()

            if len(text) <= self.max_chapter_length:
                processed_chapters.append(chapter)
            else:
                chunks = []
                words = text.split()
                current_chunk: list[str] = []
                current_length = 0

                for word in words:
                    word_length = len(word) + 1
                    if current_length + word_length > self.max_chapter_length and current_chunk:
                        chunk_text = " ".join(current_chunk)
                        chunks.append(chunk_text)
                        current_chunk = [word]
                        current_length = word_length
                    else:
                        current_chunk.append(word)
                        current_length += word_length

                if current_chunk:
                    chunks.append(" ".join(current_chunk))

                for i, chunk_text in enumerate(chunks):
                    chunk_title = f"{chapter.title or 'Chapter'} (Part {i + 1})"
                    processed_chapters.append(
                        Chapter(
                            index=chapter.index,
                            title=chunk_title,
                            content=chunk_text,
                        )
                    )

        return processed_chapters

    def _filter_chapters(self, chapters: list[Chapter]) -> list[Chapter]:
        # B-3: chapter 数の上限を別定数で正しく評価する。
        if len(chapters) <= self.max_chapters:
            return chapters

        step = len(chapters) / self.max_chapters
        selected_indices = [int(i * step) for i in range(self.max_chapters)]

        return [chapters[i] for i in selected_indices if i < len(chapters)]
