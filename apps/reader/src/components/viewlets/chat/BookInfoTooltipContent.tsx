import { User, CalendarDays, BarChart2 } from 'lucide-react'
import React from 'react'

import { useTranslation } from '@flow/reader/hooks'

import { Progress } from '../../ui/progress'

// 共通クラスをまとめて CSS を簡素化
const iconClass = 'mt-px h-3.5 w-3.5 shrink-0'

export const BookInfoTooltipContent = ({
  title,
  author,
  pubdate,
  percentage,
}: {
  title: string
  author?: string | null
  pubdate?: string | null
  percentage?: number | null
}) => {
  const t = useTranslation('chat')
  const progressPercent = percentage ? Math.round(percentage * 100) : 0

  return (
    <div className="max-w-xs text-xs">
      <p className="break-words leading-snug">{t('book_info', { title })}</p>

      <div className="mb-2 flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <User className={iconClass} />
          <span>
            {t('author')} {author || t('not_found')}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <CalendarDays className={iconClass} />
          <span>
            {t('pubdate')} {pubdate || t('not_found')}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <BarChart2 className={iconClass} />
          <span>{t('progress')}</span>
          <Progress
            value={progressPercent}
            className="flex-1 bg-white/20 dark:bg-white/30 [&>*]:bg-green-600"
          />
          <span className="w-8 text-right text-[10px]">
            {progressPercent || t('not_found')}%
          </span>
        </div>
      </div>
    </div>
  )
}
