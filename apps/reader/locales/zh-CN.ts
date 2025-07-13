export default {
  /**
   * Actions
   */
  'action.clear': '清除',
  'action.close': '关闭',
  'action.collapse_all': '折叠全部',
  'action.expand_all': '展开全部',

  /**
   * Annotations
   */
  annotate: '标注',
  'annotation.title': '标注',
  annotations: '标注',
  definitions: '定义',
  define: '定义',
  undefine: '取消定义',
  copy_as_markdown: '复制为 Markdown',

  /**
   * Book Info
   */
  author: '作者:',
  book_info: '参考 [{title}] 的信息',
  progress: '进度:',
  pubdate: '出版日期:',
  not_found: '未找到',

  /**
   * Cache
   */
  cache: '缓存',
  'cache.clear': '清除',

  /**
   * Chat
   */
  'chat.created_at': '创建时间',
  'chat.empty_description': 'AI 将根据您正在阅读的书籍知识回答问题。',
  'chat.empty_title': '开始聊天',
  'chat.error': '发生错误',
  'chat.generating': '正在生成响应...',
  'chat.history': '聊天历史',
  'chat.history_fetch_error': '获取历史记录失败',
  'chat.keyboard_shortcut': '按 `Cmd + Enter` 或 `Ctrl + Enter` 发送',
  'chat.loading': '加载中...',
  'chat.new': '新聊天',
  'chat.no_history': '未找到历史记录',
  'chat.placeholder': '输入消息...',
  'chat.search_history': '搜索聊天历史',
  'chat.send': '发送',
  'chat.title': '聊天',
  'chat.untitled': '未命名聊天',

  /**
   * Color/Theme
   */
  color_scheme: '颜色模式',
  'color_scheme.dark': '深色',
  'color_scheme.light': '浅色',
  'color_scheme.system': '系统',
  source_color: '源色',
  background_color: '背景色',

  /**
   * CRUD Operations
   */
  create: '创建',
  update: '更新',
  delete: '删除',
  cancel: '取消',
  copy: '复制',

  /**
   * Files/Import
   */
  download: '下载',
  download_sample_book: '下载样书',
  drop_to_import: '拖放以导入',
  file_import_error_log: '文件导入中发生错误:',
  import: '导入',
  import_error: '导入过程中发生错误',
  import_error_log: '导入操作中发生错误:',
  import_failed: '导入 {count} 本书失败',
  import_partial_success: '成功导入 {success} 本书（{failed} 本失败）',
  import_success: '成功导入 {count} 本书',
  importing_books: '正在导入图书',
  remote_epub_placeholder: '输入 EPUB 文件 URL',

  /**
   * Language
   */
  language: '语言',
  'language.chinese': '简体中文',
  'language.english': 'English',
  'language.japanese': '日本語',

  /**
   * Library/Book Management
   */
  library: '图书馆',
  no_books_message: '未找到图书。请导入一些图书。',
  selected_books: '已选择 {count} 本书',
  select: '选择',
  select_all: '选择所有',
  deselect_all: '取消选择所有',
  delete_confirmation: '确认删除',
  delete_confirmation_message: '您确定要删除选中的图书吗？此操作无法撤销。',
  delete_success: '图书删除成功',

  /**
   * Loading/UI States
   */
  loading: '加载中',
  share: '分享',

  /**
   * Navigation/Section Titles
   */
  'home.title': '主页',
  'image.title': '图片',
  'podcast.title': '播客',
  'search.title': '搜索',
  'settings.title': '设置',
  'theme.title': '颜色主题',
  'timeline.title': '时间线',
  'toc.title': '目录',
  'typography.title': '排版',
  title: '标题',

  /**
   * Podcast
   */
  'podcast.audio_player.change_speed': '更改播放速度',
  'podcast.audio_player.controls': '音频控制',
  'podcast.audio_player.current_time': '当前播放时间',
  'podcast.audio_player.loading': '加载中',
  'podcast.audio_player.position': '音频播放位置',
  'podcast.audio_player.skip_back': '后退10秒',
  'podcast.audio_player.skip_forward': '前进10秒',
  'podcast.audio_player.speed': '速度',
  'podcast.audio_player.total_time': '总播放时间',
  'podcast.book_item.generate_podcast_aria_label': '生成 {name} 的播客',
  'podcast.book_item.generating_podcast_aria_label': '正在生成 {name} 的播客',
  'podcast.detail.author_unknown': '未知作者',
  'podcast.detail.back': '返回',
  'podcast.detail.download_short': '下载',
  'podcast.failed': '播客生成失败',
  'podcast.failed_description': '发生错误，请稍后再试。',
  'podcast.generate': '生成',
  'podcast.library.description': '选择一本书来生成和播放播客',
  'podcast.list.empty': '暂无播客',
  'podcast.list.retry': '重试',
  'podcast.pane.fetching_info': '正在获取播客信息',
  'podcast.pane.generate_podcast': '生成播客',
  'podcast.pane.generating': '生成中...',
  'podcast.pane.loading': '加载中',
  'podcast.pane.loading_failed': '播客加载失败',
  'podcast.pane.podcast_title': '{name}的播客',
  'podcast.pause': '暂停',
  'podcast.play': '播放',
  'podcast.retry': '重试',
  'podcast.retrying': '重试中...',
  'podcast.script': '脚本',
  'podcast.share': '分享',
  'podcast.status.processing': '生成中',

  /**
   * Search
   */
  search_in_book: '书内搜索',
  'files.result': '{n} 个结果在 {m} 个文件中',

  /**
   * Typography
   */
  font_family: '字体',
  font_size: '字号',
  font_weight: '字重',
  line_height: '行高',
  page_view: '视图',
  'page_view.double_page': '双页',
  'page_view.single_page': '单页',
  'scope.book': '书籍',
  'scope.global': '全局',
  step_down: '减少',
  step_up: '增加',
  zoom: '缩放',
} as const