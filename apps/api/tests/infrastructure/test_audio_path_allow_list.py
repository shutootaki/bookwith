"""AudioProcessor の path allow-list テスト.

H-9: `add_background_music` の `music_path` と `save_to_file` の `file_path` が
allow-list 配下のみ許容されることを確認する。実際の音声処理は行わない。
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

from src.infrastructure.external.audio import audio_processor as ap


def test_rejects_concat_protocol():
    assert ap._is_safe_bgm_path("concat:/etc/passwd") is False


def test_rejects_pipe_protocol():
    assert ap._is_safe_bgm_path("pipe:0") is False


def test_rejects_http_url():
    assert ap._is_safe_bgm_path("http://evil.example/track.mp3") is False
    assert ap._is_safe_bgm_path("https://evil.example/track.mp3") is False


def test_rejects_data_url():
    assert ap._is_safe_bgm_path("data:audio/mpeg;base64,xxx") is False


def test_rejects_rtmp_url():
    assert ap._is_safe_bgm_path("rtmp://evil/x") is False


def test_rejects_path_outside_allow_list(monkeypatch):
    # AUDIO_BGM_DIRS が空なら絶対パスでも全拒否（デフォルト動作）
    monkeypatch.setenv("AUDIO_BGM_DIRS", "")
    # /etc/passwd は通常 allow-list 配下にない
    assert ap._is_safe_bgm_path("/etc/passwd") is False


def test_accepts_path_inside_allow_list(monkeypatch, tmp_path):
    # 一時ディレクトリを allow-list に登録 + 実ファイルを作成
    monkeypatch.setenv("AUDIO_BGM_DIRS", str(tmp_path))
    bgm_file = tmp_path / "intro.mp3"
    bgm_file.write_bytes(b"fake audio")
    assert ap._is_safe_bgm_path(str(bgm_file)) is True


def test_rejects_directory_traversal_outside_allow(monkeypatch, tmp_path):
    # allow-list 配下からの ../ で外に出る場合は弾く
    monkeypatch.setenv("AUDIO_BGM_DIRS", str(tmp_path))
    outside = tmp_path.parent / "outside.mp3"
    outside.write_bytes(b"x")
    try:
        assert ap._is_safe_bgm_path(str(outside)) is False
    finally:
        outside.unlink(missing_ok=True)


def test_output_path_requires_explicit_dirs(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_OUTPUT_DIRS", "")
    assert ap._is_safe_output_path(str(tmp_path / "out.mp3")) is False


def test_output_path_within_explicit_dirs(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_OUTPUT_DIRS", str(tmp_path))
    target = tmp_path / "subdir" / "out.mp3"
    assert ap._is_safe_output_path(str(target)) is True


def test_output_path_outside_explicit_dirs(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_OUTPUT_DIRS", str(tmp_path))
    other = Path(tempfile.gettempdir()) / "evil-output.mp3"
    assert ap._is_safe_output_path(str(other)) is False
