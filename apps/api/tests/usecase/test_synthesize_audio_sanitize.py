"""SynthesizeAudioUseCase の SSML エスケープ検証.

M-9: TTS 入力の `<` `>` `&` を XML エンティティへ変換し、SSML 解釈を防止する。
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:7127")

from src.usecase.podcast.synthesize_audio_usecase import SynthesizeAudioUseCase


def test_sanitize_for_tts_escapes_angle_brackets():
    out = SynthesizeAudioUseCase._sanitize_for_tts("<break time='2s'/>hello<prosody>")
    assert "<" not in out
    assert ">" not in out
    assert "&lt;" in out
    assert "&gt;" in out
    assert "hello" in out


def test_sanitize_for_tts_escapes_ampersand():
    out = SynthesizeAudioUseCase._sanitize_for_tts("AT&T")
    assert "&amp;" in out


def test_sanitize_for_tts_strips_control_characters():
    out = SynthesizeAudioUseCase._sanitize_for_tts("ok\x00\x07\x08text")
    assert "\x00" not in out
    assert "\x07" not in out
    assert "oktext" in out


def test_sanitize_for_tts_keeps_newlines_and_tabs():
    out = SynthesizeAudioUseCase._sanitize_for_tts("line1\nline2\ttab")
    assert "\n" in out
    assert "\t" in out


def test_sanitize_for_tts_empty_string():
    assert SynthesizeAudioUseCase._sanitize_for_tts("") == ""
