import { useCallback } from 'react'

import { useSettings } from '@flow/reader/utils/state'

const DEFAULT_SOURCE_COLOR = '#0ea5e9'

// 05_safe.md でフラグされた将来の懸念: localStorage 経由で攻撃者が `theme.source` に任意文字列を
// 書き込んだ場合、`generateCss` 経由の CSS 注入の入口になり得る（CR-5 残余シナリオ）。
// 多層防御として、入出力で hex 形式（#RRGGBB）を厳密検証し、不正値はデフォルト色にフォールバックする。
const HEX_COLOR_RE = /^#[0-9a-fA-F]{6}$/

export function isValidSourceColor(value: unknown): value is string {
  return typeof value === 'string' && HEX_COLOR_RE.test(value)
}

export function useSourceColor() {
  const [{ theme }, setSettings] = useSettings()

  const setSourceColor = useCallback(
    (source: string) => {
      // 入力時にも検証。ColorPicker は通常 #RRGGBB を渡すが、API 呼び出し経路から弾く。
      if (!isValidSourceColor(source)) return
      setSettings((prev) => ({
        ...prev,
        theme: {
          ...prev.theme,
          source,
        },
      }))
    },
    [setSettings],
  )

  // 取得時にも検証。localStorage 改竄に対する読み取り側ガード。
  const stored = theme?.source
  const sourceColor = isValidSourceColor(stored) ? stored : DEFAULT_SOURCE_COLOR

  return { sourceColor, setSourceColor }
}
