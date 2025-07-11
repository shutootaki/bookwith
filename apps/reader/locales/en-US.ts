export default {
  /**
   * Home
   */
  'home.title': 'Home',
  'home.share': 'Share',
  'home.download': 'Download',
  'home.download_sample_book': 'Download sample book',
  'home.select': 'Select',
  'home.cancel': 'Cancel',
  'home.select_all': 'Select all',
  'home.deselect_all': 'Deselect all',
  'home.export': 'Export',
  'home.import': 'Import',
  'home.upload': 'Upload',
  'home.delete': 'Delete',
  'home.delete_success': 'Books successfully deleted',
  'home.delete_confirmation': 'Confirm Deletion',
  'home.delete_confirmation_message':
    'Are you sure you want to delete the selected books? This action cannot be undone.',
  'home.import_success': 'Successfully imported {count} books',
  'home.import_failed': 'Failed to import {count} books',
  'home.import_partial_success':
    'Successfully imported {success} books (failed {failed})',
  'home.import_error': 'An error occurred during import',
  'home.import_error_log': 'An error occurred during import:',
  'home.file_import_error_log': 'An error occurred during file import:',
  'home.no_books_message': 'No books found. Please import some books.',
  'home.selected_books': '{count} books selected',
  'home.importing_books': 'Importing books',
  'home.remote_epub_placeholder': 'Enter EPUB file URL',

  /**
   * Import
   */
  'import.processing': 'Processing',
  'import.processing_aria': 'Processing',
  'import.analyzing_file': 'Analyzing file...',
  'import.processing_metadata': 'Processing metadata...',
  'import.processing_content': 'Processing content...',
  'import.saving': 'Saving...',
  'import.files_processed': 'files processed',
  'import.import_status':
    '{success} books imported successfully, {failed} books failed',
  'import.please_wait': 'Please wait for import to complete...',
  'import.api_registration_failed':
    'Failed to register book to API: {filename}',
  'import.book_registration_error':
    'Error occurred while registering book ({filename}):',

  /**
   * Table of Contents
   */
  'toc.title': 'TOC',
  'toc.library': 'Library',

  /**
   * Search
   */
  'search.title': 'Search',
  'search.files.result': '{n} results in {m} sections',

  /**
   * Annotation
   */
  'annotation.title': 'Annotation',
  'annotation.definitions': 'Definitions',
  'annotation.annotations': 'Annotations',
  'annotation.copy_as_markdown': 'Copy as Markdown',

  /**
   * Image
   */
  'image.title': 'Image',

  /**
   * Timeline
   */
  'timeline.title': 'Timeline',

  /**
   * Typography
   */
  'typography.title': 'Typography',
  'typography.scope.book': 'Book',
  'typography.scope.global': 'Global',
  'typography.page_view': 'Page View',
  'typography.page_view.single_page': 'Single Page',
  'typography.page_view.double_page': 'Double Page',
  'typography.font_family': 'Font Family',
  'typography.font_size': 'Font Size',
  'typography.font_weight': 'Font Weight',
  'typography.line_height': 'Line Height',
  'typography.zoom': 'Zoom',

  /**
   * Theme
   */
  'theme.title': 'Theme',
  'theme.source_color': 'Source Color',
  'theme.background_color': 'Background Color',

  /**
   * Settings
   */
  'settings.title': 'Settings',
  'settings.language': 'Language',
  'settings.language.english': 'English',
  'settings.language.japanese': '日本語',
  'settings.language.chinese': '简体中文',
  'settings.color_scheme': 'Color Scheme',
  'settings.color_scheme.system': 'System',
  'settings.color_scheme.light': 'Light',
  'settings.color_scheme.dark': 'Dark',
  'settings.synchronization.title': 'Synchronization',
  'settings.synchronization.authorize': 'Authorize',
  'settings.synchronization.unauthorize': 'Unauthorize',
  'settings.cache': 'Cache',
  'settings.cache.clear': 'Clear',

  /**
   * Menu
   */
  'menu.copy': 'Copy',
  'menu.search_in_book': 'Search in book',
  'menu.annotate': 'Annotate',
  'menu.define': 'Define',
  'menu.undefine': 'Undefine',
  'menu.create': 'Create',
  'menu.delete': 'Delete',
  'menu.update': 'Update',

  /**
   * Action
   */
  'action.expand_all': 'Expand All',
  'action.collapse_all': 'Collapse All',
  'action.close': 'Close',
  'action.clear': 'Clear',
  'action.step_down': 'Step Down',
  'action.step_up': 'Step Up',

  /**
   * Chat
   */
  'chat.title': 'Chat',
  'chat.placeholder': 'Ask me anything',
  'chat.new_chat': 'Open New Chat',
  'chat.history': 'Chat History',
  'chat.new': 'New Chat',
  'chat.empty_title': 'Start a chat',
  'chat.empty_description':
    'AI will answer based on knowledge from the book you are reading.',
  'chat.search_history': 'Search chat history',
  'chat.no_history': 'No history found',
  'chat.keyboard_shortcut': '`Cmd + Enter` or `Ctrl + Enter` to send',
  'chat.send': 'Send',
  'chat.error': 'An error occurred',
  'chat.created_at': 'Created at',
  'chat.sending': '💬 Sending message...',
  'chat.author': 'Author:',
  'chat.progress': 'Progress:',
  'chat.generating': 'Generating response...',
  'chat.pubdate': 'Publication date:',
  'chat.not_found': 'Not found',
  'chat.book_info': 'Reference information about [{title}]',

  /**
   * Podcast
  /**
   * Podcast
   */
  'podcast.title': 'Podcast',
  'podcast.refresh': 'Refresh',
  'podcast.generate': 'Generate',
  'podcast.play': 'Play',
  'podcast.pause': 'Pause',
  'podcast.download': 'Download',
  'podcast.share': 'Share',
  'podcast.script': 'Script',
  'podcast.status.pending': 'Pending',
  'podcast.status.processing': 'Processing',
  'podcast.status.completed': 'Completed',
  'podcast.status.failed': 'Failed',

  /**
   * Global Loading Overlay
   */
  'loading_overlay.loading': 'Loading',
  'loading_overlay.importing_books': 'Importing {completed}/{total} books',
  'loading_overlay.cancel': 'Cancel',

  /**
   * Dropzone
   */
  'dropzone.drop_to_import': 'Drop to import',

  /**
   * Others
   */
  untitled: 'Untitled',
} as const
