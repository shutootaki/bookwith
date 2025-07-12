# フロントエンド ポッドキャスト機能 実装ドキュメント

## 調査結果サマリー

### 1. 技術スタック
- **Next.js 15.3.1** + **React 19.1.0**
- **TypeScript**（strict mode）
- **Tailwind CSS**（スタイリング）
- **Valtio 1.6.0**（状態管理）
- **SWR 1.3.0**（データフェッチング）
- **Radix UI**（基本コンポーネント）
- **React Icons**（アイコン）
- **Framer Motion**（アニメーション）

### 2. 既存のアーキテクチャ分析

#### レイアウト構造
```
Layout
├── SplitView
│   ├── ActivityBar/NavigationBar (サイドバー制御)
│   ├── SideBar (ViewActions表示)
│   └── Reader (メインコンテンツ)
```

#### ViewActions システム
現在のサイドバー機能：
- **toc**: 目次表示
- **chat**: チャット機能
- **search**: 検索機能
- **annotation**: 注釈機能
- **image**: 画像表示
- **timeline**: タイムライン
- **typography**: タイポグラフィ設定
- **theme**: テーマ設定

#### タブ管理システム
- **BookTab**: 書籍を表示するタブ
- **PageTab**: 設定などのページを表示するタブ
- **Group**: タブをグループ化
- **Reader**: グループを管理

#### 状態管理
- **Valtio**を使用したリアクティブな状態管理
- `reader`オブジェクトがメインの状態
- **SWR**を使用したデータフェッチング（`useLibrary`, `useBookCovers`）

#### APIクライアント
- 統一された`apiClient`関数
- 自動的なuser_id付与
- エラーハンドリング
- JSONレスポンス処理

### 3. 既存のコンポーネント分析

#### BookGrid & Book コンポーネント
- 書籍一覧の表示
- 選択状態の管理
- カバー画像の表示
- ローディング状態の表示
- 読書進捗の表示

#### ChatView コンポーネント
- PaneViewを拡張
- チャット履歴の管理
- メッセージの送受信
- ActionBarによるアクション管理

#### PaneView システム
- 基本的なペインレイアウト
- 折りたたみ可能なPane
- ActionBarによるアクション管理
- SplitViewによる分割表示

### 4. 不足している機能
- **音声再生機能**（新規実装が必要）
- **ポッドキャスト関連のコンポーネント**
- **ポッドキャスト用のAPIハンドラー**

## UX改善提案

### 1. ユーザー体験の向上
- **直感的な操作**: 書籍一覧から簡単にポッドキャストを生成
- **視覚的なフィードバック**: 生成状況を明確に表示
- **進捗表示**: 生成プロセスの透明性
- **通知システム**: 完了時の適切な通知

### 2. 具体的な改善点
1. **書籍一覧でのポッドキャスト状況表示**
   - 生成済み、生成中、未生成の視覚的区別
   - 生成進捗のプログレスバー
   
2. **ポッドキャスト専用ビュー**
   - 統合されたポッドキャスト管理画面
   - 音声プレイヤーの直感的な操作
   
3. **生成プロセスの透明性**
   - リアルタイムの進捗表示
   - エラー時の明確なメッセージ
   
4. **音声プレイヤーの機能**
   - 再生/一時停止/停止
   - シークバー
   - 再生速度調整
   - 音量調整

## 実装計画

### Phase 1: 基盤実装
1. **ポッドキャスト用APIハンドラー**
   - `src/lib/apiHandler/podcastApiHandler.ts`
   - バックエンドAPIとの通信処理

2. **ポッドキャスト用の型定義**
   - OpenAPIスキーマの拡張
   - TypeScript型の生成

3. **音声プレイヤーコンポーネント**
   - `src/components/podcast/AudioPlayer.tsx`
   - 基本的な音声再生機能

### Phase 2: ViewAction追加
1. **PodcastView実装**
   - `src/components/viewlets/PodcastView.tsx`
   - 既存のViewActionsに追加

2. **Layoutの拡張**
   - `src/components/Layout.tsx`
   - podcastアクションの追加

### Phase 3: 書籍一覧の拡張
1. **Bookコンポーネントの拡張**
   - ポッドキャスト生成ボタンの追加
   - 生成状況の表示

2. **BookGridの拡張**
   - ポッドキャスト関連の状態管理

### Phase 4: 統合とテスト
1. **状態管理の統合**
   - Valtioへのポッドキャスト状態の統合
   - リアルタイム更新の実装

2. **エラーハンドリング**
   - 生成失敗時の処理
   - ユーザーフレンドリーなエラー表示

## 実装する必要があるファイル

### 1. APIハンドラー
```typescript
// src/lib/apiHandler/podcastApiHandler.ts
export async function createPodcast(bookId: string, title?: string)
export async function getPodcastsByBook(bookId: string)
export async function getPodcastById(podcastId: string)
export async function getPodcastStatus(podcastId: string)
```

### 2. 音声プレイヤー
```typescript
// src/components/podcast/AudioPlayer.tsx
interface AudioPlayerProps {
  audioUrl: string
  title: string
  onPlay?: () => void
  onPause?: () => void
  onEnd?: () => void
}
```

### 3. ポッドキャストビュー
```typescript
// src/components/viewlets/PodcastView.tsx
export const PodcastView: React.FC<PaneViewProps>
```

### 4. ポッドキャストPane
```typescript
// src/components/viewlets/podcast/PodcastPane.tsx
// src/components/viewlets/podcast/PodcastList.tsx
// src/components/viewlets/podcast/PodcastItem.tsx
```

### 5. 状態管理
```typescript
// src/models/podcast.ts
export interface PodcastState {
  podcasts: Podcast[]
  currentPlaying?: string
  volume: number
  playbackRate: number
}
```

### 6. SWRフック
```typescript
// src/hooks/useSWR/usePodcast.ts
export function usePodcastsByBook(bookId: string)
export function usePodcastStatus(podcastId: string)
```

## 実装順序（推奨）

### Step 1: APIハンドラーの実装
1. `podcastApiHandler.ts`の作成
2. OpenAPIスキーマの更新
3. 型定義の生成

### Step 2: 基本コンポーネントの実装
1. `AudioPlayer.tsx`の実装
2. 基本的な音声再生機能

### Step 3: ViewActionの追加
1. `PodcastView.tsx`の実装
2. `Layout.tsx`の更新
3. ViewActionsへの追加

### Step 4: 書籍一覧の拡張
1. `Book.tsx`の拡張
2. ポッドキャスト生成ボタンの追加
3. 生成状況の表示

### Step 5: 状態管理の統合
1. Valtioへのポッドキャスト状態の追加
2. リアルタイム更新の実装

### Step 6: エラーハンドリングとUI改善
1. エラー表示の実装
2. ローディング状態の改善
3. 通知システムの実装

## 技術的な考慮事項

### 1. 音声再生
- HTML5 Audio APIを使用
- 再生状態の管理
- メモリリークの防止

### 2. リアルタイム更新
- SWRのリアルタイム更新機能
- ポーリングによる状態同期

### 3. パフォーマンス
- 音声ファイルの遅延読み込み
- コンポーネントの最適化

### 4. アクセシビリティ
- キーボードナビゲーション
- スクリーンリーダー対応
- ARIA属性の適切な使用

## 既存システムとの整合性

### 1. 既存のパターンに従う
- PaneViewの使用
- ActionBarの活用
- 既存のスタイルシステム

### 2. 一貫性の保持
- 既存のコンポーネントスタイル
- エラーハンドリングパターン
- 状態管理パターン

### 3. 拡張性の確保
- 将来的な機能追加への対応
- モジュラーな設計
- 再利用可能なコンポーネント

## 実装完了レポート

### 実装された機能

#### ✅ Phase 1: APIハンドラーとスキーマ
- `podcastApiHandler.ts` - 完全なAPIハンドラー実装
- `usePodcast.ts` - SWRフック実装
- OpenAPIスキーマ更新（手動追加）
- ポーリング機能付きステータス取得

#### ✅ Phase 2: コンポーネント実装
- `AudioPlayer.tsx` - フル機能音声プレイヤー
- `PodcastList.tsx` - ポッドキャスト一覧表示
- `PodcastDetail.tsx` - 詳細表示・台本表示
- `PodcastPane.tsx` - メインコンテナ

#### ✅ Phase 3: ViewAction統合
- `PodcastView.tsx` - ViewAction対応
- `Layout.tsx` - ポッドキャストアクションの追加
- 翻訳ファイル更新（日本語）
- アイコン追加（MdPodcasts）

#### ✅ Phase 4: Book拡張
- `Book.tsx` - ポッドキャスト状態表示とボタン追加
- `BookGrid.tsx` - プロパティ追加
- `LibraryContainer.tsx` - ポッドキャストボタン有効化
- 視覚的な状態インジケーター

#### ✅ Phase 5: Valtio統合
- `reader.ts` - ポッドキャスト状態管理の追加
- グローバル音声再生状態
- リアクティブな状態更新
- 音量・再生速度管理

#### ✅ Phase 6: UI改善
- エラーハンドリング強化
- アクセシビリティ対応（ARIA属性）
- キーボードナビゲーション
- ローディング状態の改善

### 実装されたコンポーネント一覧

```
src/
├── components/
│   └── podcast/
│       ├── AudioPlayer.tsx      # 音声プレイヤー
│       ├── PodcastDetail.tsx    # 詳細表示
│       ├── PodcastList.tsx      # 一覧表示
│       ├── PodcastPane.tsx      # メインコンテナ
│       └── index.ts             # エクスポート
├── hooks/
│   └── useSWR/
│       └── usePodcast.ts        # SWRフック
├── lib/
│   └── apiHandler/
│       └── podcastApiHandler.ts # APIハンドラー
└── models/
    └── reader.ts                # 状態管理拡張
```

### 主要機能

1. **ポッドキャスト生成**
   - 書籍からワンクリックでポッドキャスト生成
   - バックグラウンド処理
   - リアルタイム進捗表示

2. **音声再生**
   - HTML5 Audio API使用
   - 再生/一時停止/シーク機能
   - 音量調整
   - 10秒スキップ機能

3. **状態管理**
   - Valtioによるリアクティブ状態
   - グローバル音声状態
   - 複数コンポーネント間での状態同期

4. **UX機能**
   - ローディング状態表示
   - エラーハンドリング
   - Toast通知
   - 視覚的ステータスインジケーター

5. **アクセシビリティ**
   - ARIA属性完備
   - キーボードナビゲーション
   - スクリーンリーダー対応

### 技術的特徴

- **TypeScript**: 完全型安全
- **React 19**: 最新React機能活用
- **Valtio**: リアクティブ状態管理
- **SWR**: 効率的データフェッチング
- **Tailwind CSS**: 一貫したスタイリング
- **Framer Motion**: スムーズアニメーション

### 次のステップ（推奨）

1. **テスト**: 単体テスト・統合テストの追加
2. **パフォーマンス**: 音声ファイルの最適化
3. **機能拡張**: 再生速度調整、プレイリスト機能
4. **国際化**: 英語・中国語翻訳の追加

## 結論

既存のBookWithアーキテクチャを最大限活用し、段階的な実装により、高品質なポッドキャスト機能を実現しました。全6フェーズの実装により、ユーザー体験を大幅に向上させるポッドキャスト機能が完成しています。

各機能は既存のコードパターンに従って実装されており、保守性と拡張性を確保しています。