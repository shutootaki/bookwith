export default {
  /**
   * Home
   */
  'home.title': 'ホーム',
  'home.share': '共有',
  'home.download': 'ダウンロード',
  'home.download_sample_book': 'サンプルブックをダウンロード',
  'home.select': '選択',
  'home.cancel': 'キャンセル',
  'home.select_all': 'すべて選択',
  'home.deselect_all': 'すべて選択解除',
  'home.export': 'エクスポート',
  'home.import': 'インポート',
  'home.upload': 'アップロード',
  'home.delete': '削除',
  'home.delete_success': '本が正常に削除されました',
  'home.delete_confirmation': '削除の確認',
  'home.delete_confirmation_message':
    '選択した本を削除してもよろしいですか？この操作は取り消せません。',
  'home.import_success': '{count}冊の本を正常にインポートしました',
  'home.import_failed': '{count}冊の本のインポートに失敗しました',
  'home.import_partial_success':
    '{success}冊の本を正常にインポートしました（{failed}冊失敗）',
  'home.import_error': 'インポート中にエラーが発生しました',
  'home.import_error_log': 'インポート中にエラーが発生しました:',
  'home.file_import_error_log': 'ファイルのインポート中にエラーが発生しました:',
  'home.no_books_message': '本が見つかりません。本をインポートしてください。',
  'home.selected_books': '{count}冊選択中',
  'home.importing_books': '本をインポート中',
  'home.remote_epub_placeholder': 'EPUBファイルのURLを入力',

  /**
   * Import
   */
  'import.processing': '処理中',
  'import.processing_aria': '処理中',
  'import.analyzing_file': 'ファイルを分析中...',
  'import.processing_metadata': 'メタデータを処理中...',
  'import.processing_content': 'コンテンツを処理中...',
  'import.saving': '保存中...',
  'import.files_processed': 'ファイル処理済み',
  'import.import_status': '{success}冊の本を正常にインポート、{failed}冊失敗',
  'import.please_wait': 'インポートが完了するまでお待ちください...',
  'import.api_registration_failed': 'APIへの書籍登録に失敗しました: {filename}',
  'import.book_registration_error':
    '書籍の登録中にエラーが発生しました ({filename}):',

  /**
   * Table of Contents
   */
  'toc.title': '目次',
  'toc.library': 'ライブラリ',

  /**
   * Search
   */
  'search.title': '検索',
  'search.files.result': '{m}セクションに{n}件の結果',

  /**
   * Annotation
   */
  'annotation.title': '注釈',
  'annotation.definitions': '定義',
  'annotation.annotations': '注釈',
  'annotation.copy_as_markdown': 'Markdownとしてコピー',

  /**
   * Image
   */
  'image.title': '画像',

  /**
   * Timeline
   */
  'timeline.title': 'タイムライン',

  /**
   * Typography
   */
  'typography.title': 'タイポグラフィ',
  'typography.scope.book': '本',
  'typography.scope.global': 'グローバル',
  'typography.page_view': 'ページビュー',
  'typography.page_view.single_page': 'シングルページ',
  'typography.page_view.double_page': 'ダブルページ',
  'typography.font_family': 'フォントファミリー',
  'typography.font_size': 'フォントサイズ',
  'typography.font_weight': 'フォントウェイト',
  'typography.line_height': '行の高さ',
  'typography.zoom': 'ズーム',

  /**
   * Theme
   */
  'theme.title': 'テーマ',
  'theme.source_color': 'ソースカラー',
  'theme.background_color': '背景色',

  /**
   * Settings
   */
  'settings.title': '設定',
  'settings.language': '言語',
  'settings.language.english': 'English',
  'settings.language.japanese': '日本語',
  'settings.language.chinese': '简体中文',
  'settings.color_scheme': 'カラースキーム',
  'settings.color_scheme.system': 'システム',
  'settings.color_scheme.light': 'ライト',
  'settings.color_scheme.dark': 'ダーク',
  'settings.synchronization.title': '同期',
  'settings.synchronization.authorize': '認証',
  'settings.synchronization.unauthorize': '認証解除',
  'settings.cache': 'キャッシュ',
  'settings.cache.clear': 'クリア',

  /**
   * Menu
   */
  'menu.copy': 'コピー',
  'menu.search_in_book': '本内検索',
  'menu.annotate': '注釈',
  'menu.define': '定義',
  'menu.undefine': '定義解除',
  'menu.create': '作成',
  'menu.delete': '削除',
  'menu.update': '更新',

  /**
   * Action
   */
  'action.expand_all': 'すべて展開',
  'action.collapse_all': 'すべて折りたたむ',
  'action.close': '閉じる',
  'action.clear': 'クリア',
  'action.step_down': 'ステップダウン',
  'action.step_up': 'ステップアップ',

  /**
   * Chat
   */
  'chat.title': 'チャット',
  'chat.placeholder': '何でも聞いてください',
  'chat.new_chat': '新しいチャットを開く',
  'chat.history': 'チャット履歴',
  'chat.new': '新規チャット',
  'chat.empty_title': 'チャットを開始',
  'chat.empty_description': 'AIは読んでいる本の知識に基づいて回答します。',
  'chat.search_history': 'チャット履歴を検索',
  'chat.no_history': '履歴が見つかりません',
  'chat.keyboard_shortcut': '`Cmd + Enter` または `Ctrl + Enter` で送信',
  'chat.send': '送信',
  'chat.error': 'エラーが発生しました',
  'chat.created_at': '作成日時',
  'chat.sending': '💬 メッセージを送信中...',
  'chat.author': '著者:',
  'chat.progress': '進捗:',
  'chat.generating': '応答を生成中...',
  'chat.pubdate': '出版日:',
  'chat.not_found': '取得できませんでした',
  'chat.book_info': '[{title}] の情報を参照します',

  /**
   * Global Loading Overlay
   */
  'loading_overlay.loading': '読み込み中',
  'loading_overlay.importing_books': '{completed}/{total}冊をインポート中',
  'loading_overlay.cancel': 'キャンセル',

  /**
   * Dropzone
   */
  'dropzone.drop_to_import': 'ドロップしてインポート',

  /**
   * Others
   */
  untitled: '無題',
} as const
