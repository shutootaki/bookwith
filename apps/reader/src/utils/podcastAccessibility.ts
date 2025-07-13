import { PODCAST_KEYBOARD_SHORTCUTS } from '../constants/podcast'

/**
 * ポッドキャストコンポーネント用のアクセシビリティユーティリティ
 */

/**
 * オーディオプレイヤーのARIA属性を生成
 */
export const getAudioPlayerAriaProps = (
  isPlaying: boolean,
  currentTime: number,
  duration: number,
) => {
  return {
    'aria-label': 'Podcast audio player',
    'aria-live': 'polite' as const,
    'aria-current': isPlaying ? 'true' : 'false',
    'aria-valuenow': currentTime,
    'aria-valuemin': 0,
    'aria-valuemax': duration,
  }
}

/**
 * ポッドキャスト状態のARIAラベルを生成
 */
export const getPodcastStatusAriaLabel = (
  status: string,
  title: string,
): string => {
  const statusLabels: Record<string, string> = {
    COMPLETED: 'Completed',
    PROCESSING: 'Processing',
    FAILED: 'Failed',
    PENDING: 'Pending',
  }

  return `${title} - Status: ${statusLabels[status] || status}`
}

/**
 * キーボードショートカットのヘルプテキストを生成
 */
export const getKeyboardShortcutHelp = (): string => {
  return `
    Keyboard shortcuts:
    ${PODCAST_KEYBOARD_SHORTCUTS.PLAY_PAUSE}: Play/Pause
    ${PODCAST_KEYBOARD_SHORTCUTS.SKIP_BACK}: Skip back 10 seconds
    ${PODCAST_KEYBOARD_SHORTCUTS.SKIP_FORWARD}: Skip forward 10 seconds
    ${PODCAST_KEYBOARD_SHORTCUTS.VOLUME_UP}: Increase volume
    ${PODCAST_KEYBOARD_SHORTCUTS.VOLUME_DOWN}: Decrease volume
    ${PODCAST_KEYBOARD_SHORTCUTS.MUTE_TOGGLE}: Toggle mute
    ${PODCAST_KEYBOARD_SHORTCUTS.SPEED_UP}: Increase speed
    ${PODCAST_KEYBOARD_SHORTCUTS.SPEED_DOWN}: Decrease speed
  `.trim()
}

/**
 * フォーカストラップ用のaria属性を生成
 */
export const getFocusTrapAriaProps = (isActive: boolean) => {
  return {
    'aria-modal': isActive ? 'true' : 'false',
    'aria-hidden': !isActive ? 'true' : 'false',
  }
}

/**
 * アクションボタンのARIAラベルを生成
 */
export const getActionButtonAriaLabel = (
  action: string,
  context?: string,
): string => {
  const baseLabel = action
  return context ? `${baseLabel} for ${context}` : baseLabel
}

/**
 * スクリーンリーダー用の非表示テキストを生成
 */
export const getScreenReaderOnlyText = (text: string): string => {
  return `<span class="sr-only">${text}</span>`
}

/**
 * ポッドキャストリストのARIA属性を生成
 */
export const getPodcastListAriaProps = () => {
  return {
    role: 'list',
    'aria-label': 'Podcast episodes',
  }
}

/**
 * ポッドキャストアイテムのARIA属性を生成
 */
export const getPodcastItemAriaProps = (
  title: string,
  index: number,
  total: number,
) => {
  return {
    role: 'listitem',
    'aria-label': `${title}, ${index + 1} of ${total}`,
    'aria-setsize': total,
    'aria-posinset': index + 1,
  }
}
