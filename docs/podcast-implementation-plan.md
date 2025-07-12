# ポッドキャスト自動生成機能 実装計画

**作成日**: 2025-07-09  
**プロジェクト**: BookWith  
**機能**: EPUB 書籍からポッドキャスト音声を自動生成

## 1. 機能概要

- EPUB 形式の書籍から 5-10 分のポッドキャスト音声（MP3）を自動生成
- LLM 同士の対話形式で本の要旨を解説
- Google Gemini（要約・台本生成）と Google Cloud TTS（音声合成）を使用
- 非同期処理により、ユーザーは生成完了を待たずに他の操作が可能

## 2. 技術スタック

- **LLM**: Google Gemini 2.5 Pro（要約）/ Flash（台本生成）
- **TTS**: Google Cloud Text-to-Speech Studio Multi-speaker + Neural2 JA
- **音声処理**: pydub + ffmpeg
- **ストレージ**: GCS エミュレーター（開発環境）
- **非同期処理**: FastAPI BackgroundTasks / Celery（将来的な拡張）

## 3. 実装アーキテクチャ（DDD 準拠）

### 3.1 ドメイン層 (`src/domain/podcast/`)

#### エンティティ

```python
# entities/podcast.py
- Podcast:
  - id: PodcastId
  - book_id: BookId
  - user_id: UserId
  - title: str
  - audio_url: Optional[str]
  - status: PodcastStatus
  - script: Optional[PodcastScript]
  - created_at: datetime
  - updated_at: datetime
  - error_message: Optional[str]
```

#### 値オブジェクト

```python
# value_objects/
- PodcastId: UUID型のID
- PodcastStatus: Enum (PENDING, PROCESSING, COMPLETED, FAILED)
- PodcastScript: 台本データ（話者とテキストのリスト）
- SpeakerRole: Enum (HOST, GUEST)  # 話者識別子
```

#### リポジトリインターフェース

```python
# repositories/podcast_repository.py
- PodcastRepository:
  - save(podcast: Podcast) -> Podcast
  - find_by_id(podcast_id: PodcastId) -> Optional[Podcast]
  - find_by_book_id(book_id: BookId) -> List[Podcast]
  - update_status(podcast_id: PodcastId, status: PodcastStatus, audio_url: Optional[str] = None)
```

### 3.2 ユースケース層 (`src/usecase/podcast/`)

#### ユースケース

```python
# commands/
- CreatePodcastCommand: ポッドキャスト作成コマンド
  - execute(book_id: BookId, user_id: UserId) -> PodcastId

# queries/
- FindPodcastByIdQuery: ID検索
- FindPodcastsByBookIdQuery: 書籍ID検索
- GetPodcastStatusQuery: ステータス確認
```

#### サービス

```python
# services/
- PodcastGenerationService: ポッドキャスト生成の統合サービス
  - generate(book_id: BookId, podcast_id: PodcastId) -> None

- EpubExtractorService: EPUB章抽出
  - extract_chapters(epub_path: str) -> List[Chapter]

- ChapterSummarizerService: 章要約生成
  - summarize_chapters(chapters: List[Chapter]) -> str

- ScriptGeneratorService: 台本生成
  - generate_script(summary: str) -> PodcastScript

- AudioSynthesisService: 音声合成
  - synthesize(script: PodcastScript) -> bytes

- AudioProcessorService: 音声後処理
  - process_audio(audio_data: bytes) -> bytes
```

### 3.3 インフラストラクチャ層 (`src/infrastructure/`)

#### データベース実装

```python
# postgres/podcast/
- models/podcast_orm.py: SQLAlchemyモデル
- dtos/podcast_dto.py: DTOクラス
- repositories/podcast_repository_impl.py: リポジトリ実装
```

#### 外部サービスクライアント

```python
# external/
- gemini/
  - gemini_client.py: Gemini API クライアント
  - prompts/: プロンプトテンプレート

- cloud_tts/
  - tts_client.py: Cloud TTS クライアント
  - markup_builder.py: MultiSpeakerMarkup生成
```

#### ストレージ

```python
# storage/
- gcs_client.py: GCSエミュレータークライアント
```

### 3.4 プレゼンテーション層 (`src/presentation/api/`)

#### API エンドポイント

```python
# handlers/podcast_api_route_handler.py
- POST /podcasts/create: ポッドキャスト作成開始
- GET /podcasts/{podcast_id}: ポッドキャスト詳細取得
- GET /podcasts/book/{book_id}: 書籍のポッドキャスト一覧
- GET /podcasts/{podcast_id}/status: 処理状態確認
```

#### スキーマ

```python
# schemas/podcast_schema.py
- CreatePodcastRequest
- PodcastResponse
- PodcastStatusResponse
```

## 4. データベース設計

### podcasts テーブル

```sql
CREATE TABLE podcasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    audio_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    script JSONB,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_podcasts_book_id ON podcasts(book_id);
CREATE INDEX idx_podcasts_user_id ON podcasts(user_id);
CREATE INDEX idx_podcasts_status ON podcasts(status);
```

## 5. 実装手順

### Phase 1: 基盤構築

1. ドメインモデルの実装
2. データベーステーブルとマイグレーション作成
3. リポジトリインターフェースと実装
4. 基本的なユースケース実装

### Phase 2: 外部サービス統合

1. Gemini API クライアント実装
2. Cloud TTS クライアント実装
3. GCS エミュレータークライアント実装
4. プロンプトテンプレート作成

### Phase 3: コア機能実装

1. EPUB 抽出サービス
2. 章要約サービス
3. 台本生成サービス
4. 音声合成サービス
5. 音声処理サービス

### Phase 4: API 実装

1. API エンドポイント実装
2. スキーマ定義
3. エラーハンドリング
4. 非同期処理の統合

### Phase 5: テストと最適化

1. ユニットテスト作成
2. 統合テスト作成
3. パフォーマンス最適化
4. エラーハンドリングの改善

## 6. 設定項目

### 環境変数 (.env)

```env
# Gemini API
GEMINI_API_KEY=your-api-key
GEMINI_PRO_MODEL=gemini-2.5-pro-latest
GEMINI_FLASH_MODEL=gemini-2.5-flash-latest

# Google Cloud TTS
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
GCP_PROJECT_ID=your-project-id

# Podcast Generation
PODCAST_MAX_DURATION_SECONDS=600
PODCAST_TARGET_WORDS=1000
PODCAST_AUDIO_BITRATE=192
PODCAST_AUDIO_SAMPLE_RATE=44100

# Storage
GCS_BUCKET_NAME=dev-bucket
STORAGE_EMULATOR_HOST=http://localhost:4443
```

### AppConfig 拡張

```python
# src/config/app_config.py
class PodcastConfig(BaseModel):
    gemini_api_key: str
    gemini_pro_model: str = "gemini-2.5-pro-latest"
    gemini_flash_model: str = "gemini-2.5-flash-latest"
    max_duration_seconds: int = 600
    target_words: int = 1000
    audio_bitrate: int = 192
    audio_sample_rate: int = 44100
    gcs_bucket_name: str = "dev-bucket"
```

## 7. 非機能要件対応

### エラーハンドリング

- 各処理ステップでのエラーをキャッチし、podcast.status を FAILED に更新
- error_message フィールドに詳細なエラー情報を保存
- ユーザーへの適切なエラーメッセージ返却

### パフォーマンス

- 非同期処理により即座にレスポンスを返却
- 長時間処理のタイムアウト設定（540 秒）
- キャッシュの活用（将来的な拡張）

### セキュリティ

- ユーザー認証によるアクセス制御
- 生成されたファイルへの適切なアクセス権限設定
- API キーの安全な管理

## 8. テスト戦略

### ユニットテスト

- 各サービスクラスの個別テスト
- ドメインロジックのテスト
- 外部 API のモック化

### 統合テスト

- エンドツーエンドのポッドキャスト生成フロー
- API エンドポイントのテスト
- データベース操作のテスト

### 手動テスト

- 実際の EPUB ファイルでの動作確認
- 生成された音声ファイルの品質確認
- UI との統合確認

## 9. 今後の拡張案

- 複数言語対応（英語以外の書籍）
- カスタマイズ可能な話者設定
- BGM 追加オプション
- 生成済みポッドキャストの編集機能
- ポッドキャスト配信プラットフォームとの連携

## 10. 実装上の注意点

1. **MultiSpeakerMarkup 制限**

   - 最大 2 話者まで
   - SSML との併用不可
   - 5000 文字制限への対応

2. **非同期処理**

   - 現在は FastAPI の BackgroundTasks を使用
   - 将来的に Celery への移行を検討

3. **音声品質**

   - サンプルレート: 24kHz（合成時）→ 44.1kHz（最終出力）
   - ビットレート: 192kbps
   - クロスフェード: 0（セグメント間）

4. **エラーリトライ**
   - API 呼び出しのリトライ機構
   - 部分的な失敗時の復旧処理
