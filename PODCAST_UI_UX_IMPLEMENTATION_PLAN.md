# Podcast UI/UX 実装計画

## 仕様の確認と実装計画の対応

### 1. ✅ メイン画面で本を開いていない場合の表示
- **仕様**: ダウンロード済みの本の一覧とアクションボタン（ポッドキャスト生成・ポッドキャスト再生）を表示する
- **現状**: LibraryPodcastView.tsxで実装済み（PodcastPaneの69-71行目で制御）

### 2. ✅ ポッドキャスト再生ボタンから再生詳細画面への遷移
- **仕様**: ポッドキャスト再生を押したら再生詳細画面に遷移する
- **現状**: LibraryPodcastView.tsxの28-41行目で実装済み

### 3. ✅ 再生詳細画面のコンポーネント
- **仕様**: 進捗シークバー、音量調節バー、台本表示ボタンなどを表示
- **現状**: 
  - 進捗シークバー: AudioPlayer.tsx（90-97行目）で実装済み
  - 音量調節: VolumeControl.tsx（119-124行目）で実装済み
  - 台本表示ボタン: PodcastDetail.tsx（91-100行目）で実装済み
  - その他: 再生速度調整（SpeedControl）、スキップボタンも実装済み

### 4. ❌ 再生ボタンを押してもメイン画面の本は変更しない
- **仕様**: 再生ボタンを押しても、メイン画面の本は変更せず、stateを分離しておくこと
- **問題**: 
  - LibraryPodcastView.tsxの60-62行目で`reader.addTab(book)`を呼び出している
  - これにより本のタイトルをクリックすると本が開いてしまう
- **対応**: 本のタイトルクリック時の動作を削除または変更する必要がある

### 5. ✅ PodcastList.tsxの削除とLibraryPodcastViewからの遷移
- **仕様**: PodcastList.tsxを削除し、LibraryPodcastView.tsxの再生ボタンをクリックしたらPodcastDetail.tsxが表示される
- **現状**: すでに実装されているが、PodcastList.tsxはまだPodcastPane.tsxで使用されている（193-199行目）

### 6. ❌ PodcastDetail.tsxのボタンのアイコン化
- **仕様**: 台本、DL、共有ボタンはすべてアイコンボタンで表示し、ラベルを削除する
- **現状**: 
  - 台本ボタン: 98行目にラベル「{t('podcast.script')}」
  - DLボタン: 111-113行目にラベル「{t('podcast.detail.download_short')}」
  - 共有ボタン: 123行目にラベル「{t('podcast.share')}」
- **対応**: すべてのボタンからラベルテキストを削除

### 7. ❌ LibraryPodcastView.tsxのレスポンシブ対応
- **仕様**: レスポンシブに対応し、既存のUIとの整合性・一貫性を重要視する
- **現状**: レスポンシブデザインが実装されていない
- **対応**: 
  - グリッドレイアウトの導入（sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3など）
  - 既存コンポーネントのレスポンシブパターンに合わせる

## 実装手順

### Phase 1: 状態管理の修正
1. LibraryPodcastView.tsxから本のタイトルクリック時の`onOpenBook`動作を削除
2. BookPodcastItem.tsxの本タイトルクリック部分を非インタラクティブに変更

### Phase 2: UI/UXの改善
1. PodcastDetail.tsxのボタンをアイコンのみに変更
   - ラベルテキストを削除
   - aria-labelは維持（アクセシビリティ）
   - ツールチップの追加を検討

2. LibraryPodcastView.tsxのレスポンシブ対応
   - グリッドレイアウトの実装
   - ブレークポイント: sm（640px）、md（768px）、lg（1024px）
   - モバイルファーストアプローチ

### Phase 3: 不要なコンポーネントの削除
1. PodcastList.tsxの削除
2. PodcastPane.tsxでPodcastListの使用箇所をBookPodcastItemに置き換え

### Phase 4: 最終調整
1. 全体的なUIの一貫性チェック
2. アニメーションの統一（Framer Motion）
3. カラーテーマの統一（text-foreground/text-muted-foreground）
4. アクセシビリティの確認（aria-label、キーボードナビゲーション）

## 技術的な考慮事項

### スタイリングの一貫性
- ボタン: `variant="outline"` `size="sm"` を基本とする
- アイコンサイズ: `h-3 w-3` で統一
- 間隔: `space-y-4`（セクション間）、`space-y-3`（要素間）
- カード: `rounded-xl` `border` `shadow` を適用

### レスポンシブデザインパターン
```css
/* モバイル（デフォルト） */
grid grid-cols-1 gap-3

/* タブレット以上 */
sm:grid-cols-2

/* デスクトップ */
lg:grid-cols-3

/* 大画面 */
xl:grid-cols-4
```

### 状態管理の分離
- Podcast状態: `reader.setPodcast()` のみ使用
- Book状態: `reader.addTab()` は使用しない（ポッドキャスト機能では）
- 各状態は独立して管理される

## 質問事項

### 1. 本のタイトルのインタラクション
現在、本のタイトルをクリックすると本が開きますが、この機能を完全に削除してよいでしょうか？
それとも、別の方法（例：「本を開く」ボタンを別途追加）で本を開く機能を提供すべきでしょうか？

### 2. レスポンシブデザインの詳細
LibraryPodcastViewで表示する本の一覧は、画面サイズに応じて何列表示にすべきでしょうか？
- モバイル: 1列
- タブレット: 2列
- デスクトップ: 3列
- 大画面: 4列
この配置で問題ないでしょうか？

### 3. PodcastListの削除タイミング
PodcastList.tsxは現在PodcastPane.tsxで本を開いている時に使用されています。
この部分も含めて削除し、本を開いている時も同じUIパターンを使用すべきでしょうか？