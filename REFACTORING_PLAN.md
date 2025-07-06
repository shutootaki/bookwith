# BookWith プロジェクト リファクタリング計画書

## 概要

BookWithプロジェクトの全体的なリファクタリング計画です。外部挙動を一切変えずに、可読性・保守性・テスト容易性・パフォーマンスを向上させることを目標とします。

## 分析結果

### バックエンド（apps/api/）の問題点

#### 高優先度の問題

1. **MemoryService クラス（410行）**
   - **場所**: `src/infrastructure/memory/memory_service.py`
   - **問題**: 記憶検索、ベクトル化、要約生成の責務が混在
   - **影響**: 単一責任原則違反、テストの複雑化
   - **改善**: 3つの独立したサービスに分割

2. **MemoryVectorStore クラス（503行）**
   - **場所**: `src/infrastructure/memory/memory_vector_store.py`
   - **問題**: インデックス作成、検索、管理機能が一つのクラスに集約
   - **影響**: 変更時の影響範囲が大きい
   - **改善**: 機能別に独立したサービスに分割

3. **CreateMessageUseCase.execute メソッド（70行）**
   - **場所**: `src/usecase/message/create_message_usecase.py`
   - **問題**: プロンプト構築、ストリーミング処理、ベクトル検索が一つのメソッドに混在
   - **影響**: 可読性の低下、テストの困難さ
   - **改善**: 機能別に独立したメソッドに分割

#### 中優先度の問題

4. **PostgreSQLリポジトリの重複パターン**
   - **場所**: `src/infrastructure/postgres/*/`
   - **問題**: try-catch-rollbackパターンの重複
   - **改善**: 共通ベースリポジトリクラスの作成

5. **GCS操作の重複**
   - **場所**: `src/infrastructure/external/gcs.py`
   - **問題**: ファイル削除、署名付きURL生成処理の重複
   - **改善**: 共通ユーティリティクラスの作成

6. **API例外処理の非統一**
   - **場所**: `src/presentation/api/handlers/`
   - **問題**: ルートハンドラー間で重複する例外処理パターン
   - **改善**: 共通例外ハンドラーの作成

### フロントエンド（apps/reader/）の問題点

#### 高優先度の問題

1. **Reader.tsx コンポーネント（530行）**
   - **場所**: `src/components/Reader.tsx`
   - **問題**: グリッド表示、グループ管理、ブックペイン、イベント処理が混在
   - **影響**: 単一責任原則違反、保守性の低下
   - **改善**: 4-5個の独立したコンポーネントに分割

2. **useLoading.ts カスタムフック（125行）**
   - **場所**: `src/hooks/useLoading.ts`
   - **問題**: ローディング状態管理、プログレス管理、タスク管理が混在
   - **影響**: フックの複雑化、再利用性の低下
   - **改善**: 3つの独立したフックに分割

#### 中優先度の問題

3. **Library.tsx コンポーネント（341行）**
   - **場所**: `src/components/Library.tsx`
   - **問題**: ファイルインポート、削除、選択状態管理が混在
   - **改善**: 責務別に2-3個のコンポーネントに分割

4. **TextSelectionMenu.tsx コンポーネント（346行）**
   - **場所**: `src/components/TextSelectionMenu.tsx`
   - **問題**: レンダリングロジックとビジネスロジックが混在
   - **改善**: 2つの独立したコンポーネントに分割

5. **importHandlers.ts（191行）**
   - **場所**: `src/lib/apiHandler/importHandlers.ts`
   - **問題**: ファイル処理、プログレス管理、エラーハンドリングが混在
   - **改善**: 3つの独立したクラスに分割

## 実装計画

### Phase 1: 高優先度バックエンドリファクタリング

#### 1.1 MemoryService の分割

**対象ファイル**: `src/infrastructure/memory/memory_service.py`

**分割後の構成**:
```
src/infrastructure/memory/
├── memory_retrieval_service.py    # 記憶検索機能
├── vectorization_service.py       # ベクトル化機能  
├── summarization_service.py       # 要約生成機能
├── memory_service.py              # 統合サービス（必要最小限）
└── __init__.py
```

**分割する機能**:
- 記憶検索: `search_memories`, `get_relevant_memories`
- ベクトル化: `vectorize_content`, `create_embeddings`
- 要約生成: `generate_summary`, `create_conversation_summary`

#### 1.2 MemoryVectorStore の分割

**対象ファイル**: `src/infrastructure/memory/memory_vector_store.py`

**分割後の構成**:
```
src/infrastructure/memory/vector_store/
├── index_manager.py       # インデックス作成・管理
├── search_service.py      # 検索機能
├── store_manager.py       # データストア管理
├── base_vector_store.py   # 共通基底クラス
└── __init__.py
```

#### 1.3 CreateMessageUseCase の分割

**対象ファイル**: `src/usecase/message/create_message_usecase.py`

**分割する機能**:
- `_build_prompt()`: プロンプト構築
- `_process_streaming()`: ストリーミング処理
- `_search_vectors()`: ベクトル検索
- `_save_messages()`: メッセージ保存

### Phase 2: 高優先度フロントエンドリファクタリング

#### 2.1 Reader.tsx の分割

**対象ファイル**: `src/components/Reader.tsx`

**分割後の構成**:
```
src/components/reader/
├── ReaderGrid.tsx         # グリッド表示
├── ReaderGroup.tsx        # グループ管理
├── BookPane.tsx          # ブックペイン
├── ReaderControls.tsx    # 操作コントロール
├── ReaderEventHandlers.tsx # イベント処理
└── index.tsx             # エントリーポイント
```

#### 2.2 useLoading.ts の分割

**対象ファイル**: `src/hooks/useLoading.ts`

**分割後の構成**:
```
src/hooks/loading/
├── useLoadingState.ts     # ローディング状態管理
├── useProgressManager.ts  # プログレス管理
├── useTaskManager.ts      # タスク管理
└── index.ts              # エントリーポイント
```

### Phase 3: 中優先度リファクタリング

#### 3.1 バックエンド共通化

1. **共通ベースリポジトリクラス**
   - `src/infrastructure/postgres/base_repository.py`
   - try-catch-rollbackパターンの共通化

2. **GCS操作の共通化**
   - `src/infrastructure/external/gcs_utils.py`
   - ファイル操作の共通化

3. **API例外処理の統一**
   - `src/presentation/api/error_handlers/common_error_handler.py`
   - 統一された例外処理

#### 3.2 フロントエンド最適化

1. **Library.tsx の分割**
   - ImportManager, DeleteManager, SelectionManagerに分割

2. **TextSelectionMenu.tsx の最適化**
   - MenuRenderer, MenuLogicに分割

3. **importHandlers.ts の分割**
   - FileProcessor, ProgressManager, BookImporterに分割

### Phase 4: 低優先度リファクタリング

#### 4.1 ユーティリティ再組織化

**フロントエンド utils の統合**:
```
src/utils/
├── fileHandling/
│   ├── fileUtils.ts
│   ├── mimeTypes.ts
│   └── index.ts
├── annotation/
│   ├── colors.ts
│   ├── types.ts
│   ├── utils.ts
│   └── index.ts
└── index.ts
```

#### 4.2 バリデーション処理の改善

**Value Objectへの移譲**:
- Annotation関連のバリデーションをValue Objectに移動
- 複雑な検証ロジックの簡素化

## 実装スケジュール

### Week 1: 基盤整備
- [ ] Phase 1.1: MemoryService 分割
- [ ] Phase 1.2: MemoryVectorStore 分割
- [ ] 単体テスト実行・確認

### Week 2: 主要機能リファクタリング
- [ ] Phase 1.3: CreateMessageUseCase 分割
- [ ] Phase 2.1: Reader.tsx 分割
- [ ] 統合テスト実行・確認

### Week 3: フロントエンド最適化
- [ ] Phase 2.2: useLoading.ts 分割
- [ ] Phase 3.2: Library.tsx, TextSelectionMenu.tsx 最適化
- [ ] E2Eテスト実行・確認

### Week 4: 共通化とクリーンアップ
- [ ] Phase 3.1: バックエンド共通化
- [ ] Phase 4: ユーティリティ再組織化
- [ ] 最終テスト・品質確認

## 品質保証

### テスト戦略
1. **単体テスト**: 各リファクタリング後に実行
2. **統合テスト**: 主要機能変更後に実行
3. **E2Eテスト**: 全体リファクタリング後に実行

### 品質確認項目
- [ ] 外部挙動の変更がないことを確認
- [ ] パフォーマンス劣化がないことを確認
- [ ] コードカバレッジの維持
- [ ] 型チェック・lintの通過

### リスク管理
- **高リスク**: メモリ関連サービス、Reader.tsx
- **中リスク**: UseCase層、カスタムフック
- **低リスク**: ユーティリティ、共通化

## 成功指標

### 定量的指標
- **ファイル行数**: 400行以上のファイルを0個にする
- **関数行数**: 40行以上の関数を50%削減
- **循環的複雑度**: 10以上の関数を30%削減
- **コードカバレッジ**: 現在のレベルを維持

### 定性的指標
- **可読性**: コードレビュー時間の短縮
- **保守性**: 新機能追加時の影響範囲の局所化
- **テスト容易性**: モック作成の簡素化

## 次のステップ

1. **Phase 1.1 から開始**: MemoryService の分割
2. **各段階でテスト実行**: 品質確認を徹底
3. **継続的な改善**: リファクタリング後の継続的な品質向上

この計画に従って、BookWithプロジェクトの品質を段階的に向上させていきます。