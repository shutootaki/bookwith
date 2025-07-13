import { useCallback } from 'react'

import { useTranslation } from '../useTranslation'

interface UsePodcastShareReturn {
  handleDownload: (audioUrl: string, title: string) => Promise<void>
  handleShare: (audioUrl: string, title: string) => Promise<void>
  isWebShareSupported: boolean
  isClipboardSupported: boolean
}

/**
 * ポッドキャストのダウンロード・共有機能を管理するカスタムフック
 */
export const usePodcastShare = (): UsePodcastShareReturn => {
  const t = useTranslation()

  // ブラウザ機能のサポート状況をチェック
  const isWebShareSupported =
    typeof navigator !== 'undefined' && 'share' in navigator
  const isClipboardSupported =
    typeof navigator !== 'undefined' && 'clipboard' in navigator

  const handleDownload = useCallback(
    async (audioUrl: string, title: string) => {
      if (!audioUrl) return

      try {
        const response = await fetch(audioUrl)
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${title}.mp3`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      } catch (error) {
        console.error('Download failed:', error)
      }
    },
    [],
  )

  const handleShare = useCallback(
    async (audioUrl: string, title: string) => {
      if (!audioUrl) return

      if (isWebShareSupported) {
        try {
          await navigator.share({
            title: title,
            text: t('podcast.pane.podcast_title', { name: title }),
            url: audioUrl,
          })
        } catch (error) {
          // ユーザーがキャンセルした場合もエラーになるが、その場合は何もしない
          if (error instanceof Error && error.name !== 'AbortError') {
            // キャンセル以外のエラーの場合はクリップボードにコピー
            if (isClipboardSupported) {
              await navigator.clipboard.writeText(audioUrl)
            }
          }
        }
      } else if (isClipboardSupported) {
        await navigator.clipboard.writeText(audioUrl)
      }
    },
    [t, isWebShareSupported, isClipboardSupported],
  )

  return {
    handleDownload,
    handleShare,
    isWebShareSupported,
    isClipboardSupported,
  }
}
