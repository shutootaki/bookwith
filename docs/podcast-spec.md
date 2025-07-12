# ポッドキャスト自動生成機能 仕様書 v1.2

**作成日**: 2025‑07‑09
**作成者**: AI アーキテクトチーム
**対象リリース**: MVP (2025 Q3)

---

## 1. 目的とスコープ

EPUB 形式の書籍を入力として、5〜10  分（約 1,000  語）の**対話形式ポッドキャスト**を自動生成し、音声ファイル (MP3) をユーザーへ提供する。

- LLM: Google Gemini 2.5 Pro / Flash
- TTS: Google Cloud Text‑to‑Speech **Studio Multi‑speaker（v1beta1, MultiSpeakerMarkup）**＋ Neural2 JA
- 入力: Web UI → `.epub` アップロード
- 出力: MP3 を **GCS  エミュレーター**に保存し、UI へ URL を返却

---

## 2. システム全体構成

| レイヤ                         | 主な技術 / サービス                                                               |
| ------------------------------ | --------------------------------------------------------------------------------- |
| **0. トリガー**                | Web UI → HTTP **`POST /api/podcast/create`** (Cloud Run / Functions 2)            |
| 1. 取込 / 分割                 | EbookLib (EPUB → 章テキスト)                                                      |
| 2. 章要約                      | Gemini 2.5 **Pro**                                                                |
| 3. 台本生成                    | Gemini 2.5 **Flash** (Function‑Calling JSON)                                      |
| 4. **MultiSpeakerMarkup 生成** | Python モジュール（JSON → `MultiSpeakerMarkup.Turn[]`）                           |
| 5. 音声合成                    | Cloud TTS **`en‑US‑Studio‑MultiSpeaker`** (話者 **R / S** 最大 2 名) + Neural2 JA |
| 6. 音声結合                    | pydub + ffmpeg                                                                    |
| **7. 出力保存**                | **GCS  エミュレーター** (`localhost:4443`)                                        |

---

## 3. 処理フロー

1. **ユーザートリガー**
   Web UI が `POST /api/podcast/create` を実行。
2. **EPUB 取込**
   Epub ファイルを読み込み、章ごとに分割する。
3. **章要約**
   Gemini Pro を map‑reduce 方式で呼び出し、章要約 → 全体要約へ統合。
4. **台本生成**
   Gemini Flash へ Function‑Calling プロンプトを送り、下記 JSON 配列を取得（**話者は R と S のみ**）：

   ```json
   [
     { "speaker": "R", "text": "Hi, I'm host A …" },
     { "speaker": "S", "text": "Hello! …" }
   ]
   ```

5. **`MultiSpeakerMarkup` 生成**
   Python で `google.cloud.texttospeech_v1beta1.MultiSpeakerMarkup` を構築：

   ```python
   turns=[texttospeech.MultiSpeakerMarkup.Turn(text=t["text"],speaker=t["speaker"]) for t in script]
   synthesis_input=texttospeech.SynthesisInput(multi_speaker_markup=texttospeech.MultiSpeakerMarkup(turns=turns))
   ```

6. **音声合成**

   - ライブラリ: `google.cloud.texttospeech_v1beta1 as tts`
   - Voice: `language_code="en-US", name="en-US-Studio-MultiSpeaker"`
   - AudioConfig: `audio_encoding=MP3, sample_rate_hertz=24000`

7. **音声結合**
   生成 MP3 と日本語パート（Neural2）を `AudioSegment.append(..., crossfade=0)` で連結し、44.1 kHz / 192 kbps で再エンコード。
8. **保存 & 応答**
   `STORAGE_EMULATOR_HOST=http://localhost:4443` を利用し `podcasts/{userId}/{bookId}.mp3` に保存。
   成功時レスポンス: `{"status":"success","audioUrl":"http://localhost:4443/storage/v1/b/dev-bucket/o/podcasts%2F..."}`

---

## 4. API 仕様

### 4.1 `POST /api/podcast/create`

| 項目           | 値                                                 |
| -------------- | -------------------------------------------------- |
| 認証           | Firebase Auth Bearer Token                         |
| Content-Type   | multipart/form‑data                                |
| フィールド     | `file` (EPUB), `title` (string), `language` (enum) |
| 成功レスポンス | `200 OK` (JSON 上記)                               |
| タイムアウト   | 540 s                                              |

---

## 5. コンポーネント仕様（抜粋）

- **extract_epub.py** – EbookLib 0.18 → `chapters/{idx}.txt`
- **summarizer.py** – Gemini Pro, temperature 0.3, max_output_tokens 600
- **script_builder.py** – Gemini Flash, Function‑Calling JSON（R/S 交互）
- **markup_builder.py** – JSON → `MultiSpeakerMarkup`
- **tts_client.py** – v1beta1 client、sample_rate_hertz 24000
- **concat_audio.py** – pydub、crossfade 0

---

## 6. 非機能要件

### パフォーマンス

- 合成 API は最大 5 k  文字 / ≤ 2 speakers 制限に準拠。

## 7. 遵守事項

- **最大 2  話者** 制限を超える場合はチャンクを分割して複数 synthesize 呼び出し後に結合。
- Voice 名は厳密に `en-US-Studio-MultiSpeaker` （大文字小文字を保持）。
- `MultiSpeakerMarkup` は **SSML とは併用不可**。

## 8. 参考

- [Cloud Text-to-Speech の基本](https://cloud.google.com/text-to-speech/docs/basics?hl=ja)
- [複数の話者による会話を生成する](https://cloud.google.com/text-to-speech/docs/create-dialogue-with-multispeakers?hl=ja)
- [サンプル実装](https://github.com/coji/tts-test)
