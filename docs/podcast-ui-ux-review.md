# Podcast 機能 UI/UX レビュー (2025-07-10)

## 1. 現状把握

| 画面           | 主な構成要素                                                    | 課題点                                                                           |
| -------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Book 一覧      | 書籍カード (`Book.tsx`) にポッドキャスト生成ボタン / 状態ドット | • 状態が色だけで識別不可 (WCAG)<br/>• 進捗や詳細ツールチップ無し                 |
| Podcast Pane   | 生成ボタン・一覧・詳細 (`PodcastPane.tsx`)                      | • 生成中の残り時間/進捗不明<br/>• 更新は手動 (Refresh)                           |
| Podcast List   | 各ポッドキャストカード (`PodcastList.tsx`)                      | • 進捗バー固定 50% (ダミー)<br/>• a11y 属性不足 (`role`, `aria-live`)            |
| Podcast Detail | 再生 UI (`AudioPlayer.tsx`) & 台本                              | • シーク/音量スライダーに `aria-valuetext` 無し<br/>• コントロールが狭幅で溢れる |

## 2. ユーザー体験の観点

1. 状態可視化: 進行状況・失敗理由を直感的に把握できる
2. 操作導線: 一覧 → 再生を最短に / 現在再生中をどこでも確認
3. フィードバック: 非同期操作に残り時間・キャンセル導線
4. アクセシビリティ: 色依存排除 / キーボード操作 / `aria-live`
5. レスポンシブ: モバイル幅 320 px で操作系が崩れない

## 3. 改善方針

### 3.1 コンポーネント別

- **Book.tsx**
  - 状態ドット → アイコン + 色 + Tooltip (`Tooltip` from Radix)
  - `aria-label="podcast.status.*"` を付与
- **PodcastList.tsx**
  - 各 Podcast を個別ポーリング → 正しい進捗バー表示
  - `role="list"`/`role="listitem"`, `aria-live="polite"`
- **PodcastPane.tsx**
  - 生成ボタン押下後、カード上に残り時間バー + Cancel
- **AudioPlayer.tsx**
  - `aria-valuetext` ("再生位置 X 秒") / ボリュームにも
  - コントロールを `flex-wrap` でモバイル対応
  - 長押しスキップ実装 (UX 向上)

### 3.2 グローバル

- i18n キー流用 (既に定義済み)
- Tailwind semantic colors で状態色を集中管理

## 4. 実装ステップ

1. **調査まとめ** (本ドキュメント)
2. **UI コンポーネント改修**
   1. Book.tsx (Tooltip + アイコン化)
   2. PodcastList.tsx (a11y & progress)
   3. AudioPlayer.tsx (a11y & レスポンシブ)
3. **テスト**: Playwright によるビジュアル / a11y 回帰 (CI 自動実行)

---

> 本ドキュメントは UI/UX デザイナー視点の改善項目をまとめたものです。実装後に再レビューを行い、必要に応じて追加タスクを発行します。
