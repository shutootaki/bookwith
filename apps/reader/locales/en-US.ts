export default {
  /**
   * Actions
   */
  'action.clear': 'Clear',
  'action.close': 'Close',
  'action.collapse_all': 'Collapse All',
  'action.expand_all': 'Expand All',

  /**
   * Annotations
   */
  annotate: 'Annotate',
  'annotation.title': 'Annotation',
  annotations: 'Annotations',
  definitions: 'Definitions',
  define: 'Define',
  undefine: 'Undefine',
  copy_as_markdown: 'Copy as Markdown',

  /**
   * Book Info
   */
  author: 'Author:',
  book_info: 'Reference information about [{title}]',
  progress: 'Progress:',
  pubdate: 'Publication date:',
  not_found: 'Not found',

  /**
   * Cache
   */
  cache: 'Cache',
  'cache.clear': 'Clear',

  /**
   * Chat
   */
  'chat.created_at': 'Created at',
  'chat.empty_description': 'AI will answer based on knowledge from the book you are reading.',
  'chat.empty_title': 'Start a chat',
  'chat.error': 'An error occurred',
  'chat.generating': 'Generating response...',
  'chat.history': 'Chat History',
  'chat.history_fetch_error': 'Failed to fetch history',
  'chat.keyboard_shortcut': '`Cmd + Enter` or `Ctrl + Enter` to send',
  'chat.loading': 'Loading...',
  'chat.new': 'New Chat',
  'chat.no_history': 'No history found',
  'chat.placeholder': 'Ask me anything',
  'chat.search_history': 'Search chat history',
  'chat.send': 'Send',
  'chat.title': 'Chat',
  'chat.untitled': 'Untitled Chat',

  /**
   * Color/Theme
   */
  color_scheme: 'Color Scheme',
  'color_scheme.dark': 'Dark',
  'color_scheme.light': 'Light',
  'color_scheme.system': 'System',
  source_color: 'Source Color',
  background_color: 'Background Color',

  /**
   * CRUD Operations
   */
  create: 'Create',
  update: 'Update',
  delete: 'Delete',
  cancel: 'Cancel',
  copy: 'Copy',

  /**
   * Files/Import
   */
  download: 'Download',
  download_sample_book: 'Download sample book',
  drop_to_import: 'Drop to import',
  file_import_error_log: 'An error occurred during file import:',
  import: 'Import',
  import_error: 'An error occurred during import',
  import_error_log: 'An error occurred during import:',
  import_failed: 'Failed to import {count} books',
  import_partial_success: 'Successfully imported {success} books (failed {failed})',
  import_success: 'Successfully imported {count} books',
  importing_books: 'Importing books',
  remote_epub_placeholder: 'Enter EPUB file URL',

  /**
   * Language
   */
  language: 'Language',
  'language.chinese': '简体中文',
  'language.english': 'English',
  'language.japanese': '日本語',

  /**
   * Library/Book Management
   */
  library: 'Library',
  no_books_message: 'No books found. Please import some books.',
  selected_books: '{count} books selected',
  select: 'Select',
  select_all: 'Select all',
  deselect_all: 'Deselect all',
  delete_confirmation: 'Confirm Deletion',
  delete_confirmation_message: 'Are you sure you want to delete the selected books? This action cannot be undone.',
  delete_success: 'Books successfully deleted',

  /**
   * Loading/UI States
   */
  loading: 'Loading',
  share: 'Share',

  /**
   * Navigation/Section Titles
   */
  'home.title': 'Home',
  'image.title': 'Image',
  'podcast.title': 'Podcast',
  'search.title': 'Search',
  'settings.title': 'Settings',
  'theme.title': 'Theme',
  'timeline.title': 'Timeline',
  'toc.title': 'TOC',
  'typography.title': 'Typography',
  title: 'Title',

  /**
   * Podcast
   */
  'podcast.audio_player.change_speed': 'Change playback speed',
  'podcast.audio_player.controls': 'Audio controls',
  'podcast.audio_player.current_time': 'Current playback time',
  'podcast.audio_player.loading': 'Loading',
  'podcast.audio_player.position': 'Audio playback position',
  'podcast.audio_player.skip_back': 'Skip back 10 seconds',
  'podcast.audio_player.skip_forward': 'Skip forward 10 seconds',
  'podcast.audio_player.speed': 'Speed',
  'podcast.audio_player.total_time': 'Total playback time',
  'podcast.book_item.generate_podcast_aria_label': 'Generate podcast for {name}',
  'podcast.book_item.generating_podcast_aria_label': 'Generating podcast for {name}',
  'podcast.detail.author_unknown': 'Unknown author',
  'podcast.detail.back': 'Back',
  'podcast.detail.download_short': 'DL',
  'podcast.failed': 'Podcast generation failed',
  'podcast.failed_description': 'An error occurred. Please try again later.',
  'podcast.generate': 'Generate',
  'podcast.library.description': 'Select a book to generate and play podcasts',
  'podcast.list.empty': 'No podcasts yet',
  'podcast.list.retry': 'Retry',
  'podcast.pane.fetching_info': 'Fetching podcast information',
  'podcast.pane.generate_podcast': 'Generate Podcast',
  'podcast.pane.generating': 'Generating...',
  'podcast.pane.loading': 'Loading',
  'podcast.pane.loading_failed': 'Failed to load podcasts',
  'podcast.pane.podcast_title': 'Podcast for {name}',
  'podcast.pause': 'Pause',
  'podcast.play': 'Play',
  'podcast.retry': 'Retry',
  'podcast.retrying': 'Retrying...',
  'podcast.script': 'Script',
  'podcast.share': 'Share',
  'podcast.status.processing': 'Processing',

  /**
   * Search
   */
  search_in_book: 'Search in book',
  'files.result': '{n} results in {m} sections',

  /**
   * Typography
   */
  font_family: 'Font Family',
  font_size: 'Font Size',
  font_weight: 'Font Weight',
  line_height: 'Line Height',
  page_view: 'Page View',
  'page_view.double_page': 'Double Page',
  'page_view.single_page': 'Single Page',
  'scope.book': 'Book',
  'scope.global': 'Global',
  step_down: 'Step Down',
  step_up: 'Step Up',
  zoom: 'Zoom',
} as const