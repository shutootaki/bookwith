import React, { useMemo } from 'react'

import { useReaderSnapshot } from '../../../models'
import { ResponsiveToolTip } from '../../ResponsiveToolTip'

interface Citation {
  marker: string
  number: string
  chapter: string
  position_percent?: number | null
  location_info?: string
  is_highlight?: boolean
  cfi?: string | null
}

interface CitationTextProps {
  text: string
  citations?: Citation[]
}

// 引用マーカーを検出する正規表現（定数として定義）
const CITATION_PATTERN = /[¹²³⁴⁵⁶⁷⁸⁹★]\d*/g

export const CitationText: React.FC<CitationTextProps> = ({
  text,
  citations = [],
}) => {
  const reader = useReaderSnapshot()

  // 正規表現パターンをメモ化
  const citationPattern = useMemo(() => new RegExp(CITATION_PATTERN), [])

  // 引用をクリックしたときのハンドラ
  const handleCitationClick = (citation: Citation) => {
    const bookTab = reader.focusedBookTab
    if (!bookTab) return

    // CFIがある場合は直接ジャンプ
    if (citation.cfi) {
      bookTab.display(citation.cfi)
      return
    }

    // 位置％がある場合は計算してジャンプ
    if (
      citation.position_percent !== null &&
      citation.position_percent !== undefined
    ) {
      // 全セクションから該当位置を計算
      const targetPosition = citation.position_percent / 100
      const totalLength = bookTab.totalLength
      const targetLength = totalLength * targetPosition

      let currentLength = 0
      let targetSection = null

      // 該当するセクションを探す
      for (const section of bookTab.sections || []) {
        currentLength += section.length
        if (currentLength >= targetLength) {
          targetSection = section
          break
        }
      }

      if (targetSection) {
        bookTab.display(targetSection.href)
      }
    }
  }

  // テキストを引用マーカーで分割してレンダリング
  const renderTextWithCitations = () => {
    const parts: React.ReactNode[] = []
    let lastIndex = 0
    let match

    // 事前にMapを作成してO(1)のルックアップを実現
    const citationMap = new Map(citations.map((c) => [c.marker, c]))

    // 引用マーカーを検出してテキストを分割
    const regex = new RegExp(citationPattern)
    while ((match = regex.exec(text)) !== null) {
      const marker = match[0]
      const matchIndex = match.index

      // マーカー前のテキストを追加
      if (matchIndex > lastIndex) {
        parts.push(text.substring(lastIndex, matchIndex))
      }

      // 対応する引用情報を探す（O(1)ルックアップ）
      const citation = citationMap.get(marker)

      if (citation) {
        // 引用リンクを追加
        parts.push(
          <ResponsiveToolTip
            key={`citation-${matchIndex}`}
            content={
              <div className="max-w-xs">
                <div className="font-semibold">{citation.chapter}</div>
                {citation.position_percent !== null &&
                  citation.position_percent !== undefined && (
                    <div className="text-sm text-gray-300">
                      約{citation.position_percent}%の位置
                    </div>
                  )}
                {citation.location_info && (
                  <div className="text-sm text-gray-300">
                    {citation.location_info}
                  </div>
                )}
              </div>
            }
          >
            <sup
              className="cursor-pointer text-blue-400 transition-colors hover:text-blue-300 hover:underline"
              onClick={() => handleCitationClick(citation)}
            >
              {marker}
            </sup>
          </ResponsiveToolTip>,
        )
      } else {
        // 引用情報がない場合は通常の上付き文字として表示
        parts.push(<sup key={`sup-${matchIndex}`}>{marker}</sup>)
      }

      lastIndex = matchIndex + marker.length
    }

    // 残りのテキストを追加
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex))
    }

    return parts
  }

  // テキスト全体を処理してから改行を適用
  const processedContent = renderTextWithCitations()

  // processedContentを改行で分割して再構築
  const finalContent: React.ReactNode[] = []
  let currentLine: React.ReactNode[] = []

  processedContent.forEach((part) => {
    if (typeof part === 'string') {
      // 文字列の場合、改行で分割
      const subParts = part.split('\n')
      subParts.forEach((subPart, subIndex) => {
        if (subIndex > 0) {
          // 改行があった場合
          finalContent.push(
            <React.Fragment key={`line-${finalContent.length}`}>
              {currentLine}
            </React.Fragment>,
          )
          finalContent.push(<br key={`br-${finalContent.length}`} />)
          currentLine = []
        }
        if (subPart) {
          currentLine.push(subPart)
        }
      })
    } else {
      // React要素の場合はそのまま追加
      currentLine.push(part)
    }
  })

  // 最後の行を追加
  if (currentLine.length > 0) {
    finalContent.push(
      <React.Fragment key={`line-${finalContent.length}`}>
        {currentLine}
      </React.Fragment>,
    )
  }

  return <>{finalContent}</>
}
