# ローディングコンポーネント設計書

## 概要
ローディング中にユーザーが他の画面要素をクリックできないようにするグローバルローディングシステムの設計。

## 要件定義

### 機能要件
1. **グローバルローディングオーバーレイ**
   - アプリケーション全体をカバーする半透明のオーバーレイ
   - ローディング中は全ての操作をブロック
   - 複数の同時実行タスクに対応

2. **ローディング状態の一元管理**
   - Jotaiアトムによるグローバル状態管理
   - 各ローディングタスクの識別と追跡
   - 自動的なローディング表示の制御

3. **統一されたUI表現**
   - 一貫性のあるローディングアニメーション
   - 操作内容に応じたローディングメッセージの表示
   - プログレス表示のサポート（オプション）

### 非機能要件
1. **パフォーマンス**
   - 最小限のリレンダリング
   - 効率的な状態管理

2. **アクセシビリティ**
   - スクリーンリーダー対応
   - キーボードフォーカストラップ
   - 適切なARIA属性

3. **ユーザビリティ**
   - 即座のフィードバック
   - 明確な視覚的インジケーター
   - エラー時の適切な処理

## アーキテクチャ設計

### コンポーネント構成

```
┌─────────────────────────────────────────────────┐
│                   App Layout                    │
│  ┌───────────────────────────────────────────┐  │
│  │         GlobalLoadingOverlay              │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │      LoadingContent                  │  │  │
│  │  │  ・スピナー                          │  │  │
│  │  │  ・メッセージ                        │  │  │
│  │  │  ・プログレスバー（オプション）      │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │           Main Content                     │  │
│  │  （ユーザーコンテンツ）                   │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### アトム設計（Jotai）

```typescript
// types
interface LoadingTask {
  id: string                    // タスクの一意識別子
  message?: string              // 表示メッセージ
  progress?: {                  // プログレス情報（オプション）
    current: number
    total: number
  }
  type: 'global' | 'local'      // ローディングのスコープ
}

// atoms
import { atom } from 'jotai'
import { atomWithDefault } from 'jotai/utils'

// タスクを管理するアトム
export const loadingTasksAtom = atom<Map<string, LoadingTask>>(new Map())

// 派生アトム（計算プロパティ）
export const isGlobalLoadingAtom = atom(
  (get) => {
    const tasks = get(loadingTasksAtom)
    return Array.from(tasks.values()).some(task => task.type === 'global')
  }
)

export const activeTasksCountAtom = atom(
  (get) => get(loadingTasksAtom).size
)

export const primaryTaskAtom = atom<LoadingTask | null>(
  (get) => {
    const tasks = get(loadingTasksAtom)
    const globalTasks = Array.from(tasks.values()).filter(task => task.type === 'global')
    return globalTasks[0] || null
  }
)
```

## 実装仕様

### 1. グローバルローディングオーバーレイコンポーネント

```typescript
// components/loading/GlobalLoadingOverlay.tsx
interface GlobalLoadingOverlayProps {
  // 追加のプロパティは不要（ストアから状態を取得）
}
```

**機能仕様:**
- Jotaiアトムから状態を監視
- グローバルタスクが存在する場合のみ表示
- ポータルを使用してルート要素に直接マウント
- Framer Motionによるスムーズなアニメーション

### 2. ローディングフック

```typescript
// hooks/useLoading.ts
interface UseLoadingOptions {
  message?: string
  type?: 'global' | 'local'
  showProgress?: boolean
}

function useLoading(options?: UseLoadingOptions): {
  startLoading: (taskId?: string) => string
  updateProgress: (current: number, total: number) => void
  stopLoading: (taskId?: string) => void
  isLoading: boolean
}
```

### 3. 統合パターン

#### パターン1: API呼び出し
```typescript
const { startLoading, stopLoading } = useLoading({
  message: '本を読み込んでいます...',
  type: 'global'
})

const loadBook = async () => {
  const taskId = startLoading()
  try {
    await api.loadBook()
  } finally {
    stopLoading(taskId)
  }
}
```

#### パターン2: ファイルインポート
```typescript
const { startLoading, updateProgress, stopLoading } = useLoading({
  message: 'ファイルをインポートしています...',
  type: 'global',
  showProgress: true
})

const importFiles = async (files: File[]) => {
  const taskId = startLoading()
  for (let i = 0; i < files.length; i++) {
    updateProgress(i, files.length)
    await processFile(files[i])
  }
  stopLoading(taskId)
}
```

## UIデザイン仕様

### オーバーレイスタイル
- 背景色: `rgba(0, 0, 0, 0.5)` (半透明の黒)
- z-index: 9999（最前面）
- backdrop-filter: blur(2px)（オプション）

### ローディングコンテンツ
- 中央配置のコンテナ
- 白背景のカード（ダークモード対応）
- パディング: 24px
- 角丸: 8px
- 影: shadow-lg

### アニメーション
- フェードイン/アウト: 200ms
- スピナー回転: 1秒で1回転
- プログレスバー: スムーズな遷移

## 実装計画

### フェーズ1: 基盤構築
1. Jotaiアトムの実装（`stores/loading.ts`）
2. 基本的なローディングフックの実装（`hooks/useLoading.ts`）
3. グローバルローディングオーバーレイコンポーネントの実装

### フェーズ2: 統合
1. アプリケーションルートへのオーバーレイコンポーネントの配置
2. 既存のローディング処理の移行
   - 本のインポート処理
   - API呼び出し
   - チャット送信

### フェーズ3: 最適化
1. パフォーマンス最適化
2. アクセシビリティ対応
3. エラーハンドリングの強化

## テスト計画

### ユニットテスト
- Jotaiアトムのロジック
- useLoadingフックの動作
- コンポーネントの表示/非表示

### 統合テスト
- 複数タスクの同時実行
- エラー時の挙動
- メモリリークの確認

### E2Eテスト
- ユーザー操作のブロック確認
- アニメーションの動作確認
- アクセシビリティテスト

## 実装優先順位

1. **必須機能**（MVP）
   - グローバルローディングオーバーレイ
   - 基本的な状態管理
   - 操作ブロック機能

2. **推奨機能**
   - プログレス表示
   - カスタムメッセージ
   - アニメーション

3. **オプション機能**
   - タスクキューイング
   - タイムアウト処理
   - 詳細なエラーハンドリング

## まとめ
このローディングシステムにより、ユーザーエクスペリエンスの向上と、一貫性のあるローディング体験を提供します。Jotaiによる効率的な状態管理と、再利用可能なコンポーネント設計により、保守性と拡張性も確保されます。