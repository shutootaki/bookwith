import { useRef } from 'react'

import { LONG_PRESS } from '../constants/audio'

interface LongPressOptions {
  interval?: number
}

interface LongPressHandlers {
  onPointerDown: () => void
  onPointerUp: () => void
  onPointerLeave: () => void
}

/**
 * 長押し操作を処理するカスタムフック
 * @param action 実行する関数
 * @param options オプション設定
 * @returns イベントハンドラー
 */
export const useLongPress = (
  action: () => void,
  options: LongPressOptions = {},
): LongPressHandlers => {
  const timer = useRef<NodeJS.Timeout | null>(null)
  const { interval = LONG_PRESS.DEFAULT_INTERVAL } = options

  const start = () => {
    // 最初に一度実行
    action()
    // インターバルで継続実行
    timer.current = setInterval(action, interval)
  }

  const stop = () => {
    if (timer.current) {
      clearInterval(timer.current)
      timer.current = null
    }
  }

  return {
    onPointerDown: start,
    onPointerUp: stop,
    onPointerLeave: stop,
  }
}
