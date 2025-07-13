export default {
  /**
   * Common
   */
  'common.loading': '加载中',
  'common.retry': '重试',
  'common.retrying': '重试中...',
  'common.created_at': '创建时间',
  'common.updated_at': '更新时间',
  'common.cancel': '取消',

  /**
   * Home
   */
  'home.title': '主页',
  'home.share': '分享',
  'home.download': '下载',
  'home.download_sample_book': '下载样书',
  'home.select': '选择',
  'home.cancel': '取消', // TODO: 使用 'common.cancel'
  'home.select_all': '选择所有',
  'home.deselect_all': '取消选择所有',
  'home.export': '导出',
  'home.import': '导入',
  'home.upload': '上传',
  'home.delete': '删除',
  'home.delete_success': '图书删除成功',
  'home.delete_confirmation': '确认删除',
  'home.delete_confirmation_message':
    '您确定要删除选中的图书吗？此操作无法撤销。',
  'home.import_success': '成功导入 {count} 本书',
  'home.import_failed': '导入 {count} 本书失败',
  'home.import_partial_success': '成功导入 {success} 本书（{failed} 本失败）',
  'home.import_error': '导入过程中发生错误',
  'home.import_error_log': '导入操作中发生错误:',
  'home.file_import_error_log': '文件导入中发生错误:',
  'home.no_books_message': '未找到图书。请导入一些图书。',
  'home.selected_books': '已选择 {count} 本书',
  'home.importing_books': '正在导入图书',
  'home.remote_epub_placeholder': '输入 EPUB 文件 URL',

  /**
   * Import
   */
  'import.processing': '处理中',
  'import.processing_aria': '处理',
  'import.analyzing_file': '正在分析文件...',
  'import.processing_metadata': '正在处理元数据...',
  'import.processing_content': '正在处理内容...',
  'import.saving': '正在保存...',
  'import.files_processed': '个文件已处理',
  'import.import_status': '{success} 本书导入成功，{failed} 本失败',
  'import.please_wait': '请等待导入完成...',
  'import.api_registration_failed': 'API 书籍注册失败: {filename}',
  'import.book_registration_error': '书籍注册时发生错误 ({filename}):',

  /**
   * Table of Contents
   */
  'toc.title': '目录',
  'toc.library': '图书馆',

  /**
   * Search
   */
  'search.title': '搜索',
  'search.files.result': '{n} 个结果在 {m} 个文件中',

  /**
   * Annotation
   */
  'annotation.title': '标注',
  'annotation.definitions': '定义',
  'annotation.annotations': '标注',
  'annotation.copy_as_markdown': '复制为 Markdown',

  /**
   * Image
   */
  'image.title': '图片',

  /**
   * Timeline
   */
  'timeline.title': '时间线',

  /**
   * Typography
   */
  'typography.title': '排版',
  'typography.scope.book': '书籍',
  'typography.scope.global': '全局',
  'typography.page_view': '视图',
  'typography.page_view.single_page': '单页',
  'typography.page_view.double_page': '双页',
  'typography.font_family': '字体',
  'typography.font_size': '字号',
  'typography.font_weight': '字重',
  'typography.line_height': '行高',
  'typography.zoom': '缩放',

  /**
   * Theme
   */
  'theme.title': '颜色主题',
  'theme.source_color': '源色',
  'theme.background_color': '背景色',

  /**
   * Settings
   */
  'settings.title': '设置',
  'settings.language': '语言',
  'settings.language.english': 'English',
  'settings.language.japanese': '日本語',
  'settings.language.chinese': '简体中文',
  'settings.color_scheme': '颜色模式',
  'settings.color_scheme.system': '系统',
  'settings.color_scheme.light': '浅色',
  'settings.color_scheme.dark': '深色',
  'settings.synchronization.title': '同步',
  'settings.synchronization.authorize': '授权',
  'settings.synchronization.unauthorize': '取消授权',
  'settings.cache': '缓存',
  'settings.cache.clear': '清除',

  /**
   * Menu
   */
  'menu.copy': '复制',
  'menu.search_in_book': '书内搜索',
  'menu.annotate': '标注',
  'menu.define': '定义',
  'menu.undefine': '取消定义',
  'menu.create': '创建',
  'menu.delete': '删除',
  'menu.update': '更新',

  /**
   * Action
   */
  'action.expand_all': '展开全部',
  'action.collapse_all': '折叠全部',
  'action.close': '关闭',
  'action.clear': '清除',
  'action.step_down': '减少',
  'action.step_up': '增加',

  /**
   * Chat
   */
  'chat.title': '聊天',
  'chat.placeholder': '输入消息...',
  'chat.new_chat': '新建聊天',
  'chat.history': '聊天历史',
  'chat.new': '新聊天',
  'chat.empty_title': '开始聊天',
  'chat.empty_description': 'AI 将根据您正在阅读的书籍知识回答问题。',
  'chat.search_history': '搜索聊天历史',
  'chat.no_history': '未找到历史记录',
  'chat.keyboard_shortcut': '按 `Cmd + Enter` 或 `Ctrl + Enter` 发送',
  'chat.send': '发送',
  'chat.error': '发生错误',
  'chat.created_at': '创建时间',
  'chat.sending': '💬 正在发送消息...',
  'chat.author': '作者:',
  'chat.progress': '进度:',
  'chat.generating': '正在生成响应...',
  'chat.pubdate': '出版日期:',
  'chat.not_found': '未找到',
  'chat.book_info': '参考 [{title}] 的信息',

  /**
   * Podcast
   */
  'podcast.title': '播客',
  'podcast.refresh': '刷新',
  'podcast.generate': '生成',
  'podcast.play': '播放',
  'podcast.pause': '暂停',
  'podcast.download': '下载',
  'podcast.share': '分享',
  'podcast.script': '脚本',
  'podcast.status.pending': '待机中',
  'podcast.status.processing': '生成中',
  'podcast.status.completed': '完成',
  'podcast.status.failed': '失败',
  'podcast.status.unknown': '未知',
  'podcast.failed': '播客生成失败',
  'podcast.failed_description': '发生错误，请稍后再试。',
  'podcast.retry': '重试', // TODO: 使用 'common.retry'
  'podcast.retrying': '重试中...', // TODO: 使用 'common.retrying'

  // AudioPlayer 相关
  'podcast.audio_player.playback_failed': '音频播放失败',
  'podcast.audio_player.skip_back': '后退10秒',
  'podcast.audio_player.skip_forward': '前进10秒',
  'podcast.audio_player.loading': '加载中', // TODO: 使用 'common.loading'
  'podcast.audio_player.current_time': '当前播放时间',
  'podcast.audio_player.total_time': '总播放时间',
  'podcast.audio_player.controls': '音频控制',
  'podcast.audio_player.position': '音频播放位置',
  'podcast.audio_player.speed': '速度',
  'podcast.audio_player.change_speed': '更改播放速度',

  // PodcastDetail 相关
  'podcast.detail.back': '返回',
  'podcast.detail.download_short': '下载',
  'podcast.detail.created_at': '创建时间', // TODO: 使用 'common.created_at'
  'podcast.detail.updated_at': '更新时间', // TODO: 使用 'common.updated_at'
  'podcast.detail.status': '状态',
  'podcast.detail.error': '错误',
  'podcast.detail.author_unknown': '未知作者',

  // PodcastList 相关
  'podcast.list.empty': '暂无播客',
  'podcast.list.generating': '正在生成播客...',
  'podcast.list.retry': '重试', // TODO: 使用 'common.retry'
  'podcast.list.retrying': '重试中...', // TODO: 使用 'common.retrying'
  'podcast.list.created_date': '创建时间', // TODO: 使用 'common.created_at'
  'podcast.list.updated_date': '更新时间', // TODO: 使用 'common.updated_at'
  'podcast.list.refresh': '刷新',
  'podcast.list.refreshing_aria_label': '正在刷新播客列表',
  'podcast.list.refresh_aria_label': '刷新播客列表',
  'podcast.list.play_podcast_aria_label': '播放 {title}',

  // PodcastPane 相关
  'podcast.pane.generation_started': '播客生成已开始',
  'podcast.pane.generation_failed': '播客生成失败',
  'podcast.pane.regeneration_started': '播客重新生成已开始',
  'podcast.pane.regeneration_failed': '播客重新生成失败',
  'podcast.pane.generating': '生成中...',
  'podcast.pane.generate_podcast': '生成播客',
  'podcast.pane.podcast_list': '播客列表',
  'podcast.pane.loading_failed': '播客加载失败',
  'podcast.pane.loading': '加载中', // TODO: 使用 'common.loading'
  'podcast.pane.fetching_info': '正在获取播客信息',
  'podcast.pane.library': '图书馆',
  'podcast.pane.library_description': '选择一本书来生成和播放播客',
  'podcast.pane.podcast_title': '{name}的播客',

  // Library Podcast View 相关
  'podcast.library.title': '图书馆',
  'podcast.library.description': '选择一本书来生成和播放播客',

  // Book Podcast Item 相关
  'podcast.book_item.open_book_aria_label':
    '打开 {name}{author, select, null {} other { (作者: {author})}}',
  'podcast.book_item.play_podcast_aria_label': '播放 {name} 的播客',
  'podcast.book_item.generating_podcast_aria_label': '正在生成 {name} 的播客',
  'podcast.book_item.generate_podcast_aria_label': '生成 {name} 的播客',

  /**
   * Global Loading Overlay
   */
  'loading_overlay.loading': '加载中', // TODO: 使用 'common.loading'
  'loading_overlay.importing_books': '正在导入 {completed}/{total} 本书',
  'loading_overlay.cancel': '取消', // TODO: 使用 'common.cancel'
  /**
   * Dropzone
   */
  'dropzone.drop_to_import': '拖放以导入',

  /**
   * Others
   */
  untitled: '未标题',
} as const
