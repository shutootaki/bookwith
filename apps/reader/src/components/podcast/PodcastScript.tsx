import { User } from 'lucide-react'
import React, { memo, useMemo, useRef, useEffect } from 'react'

import { useTranslation } from '../../hooks/useTranslation'
import { cn } from '../../lib/utils'
import { Avatar, AvatarFallback } from '../ui/avatar'

interface ScriptTurn {
  speaker: string
  text: string
  timestamp?: number
}

interface PodcastScriptProps {
  script: ScriptTurn[]
  currentTime?: number
  onTimeSeek?: (time: number) => void
}

const PodcastScriptComponent: React.FC<PodcastScriptProps> = ({
  script,
  currentTime,
  onTimeSeek,
}) => {
  const t = useTranslation()
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // スピーカーごとのスタイルを決定
  const speakerStyles = useMemo(() => {
    const uniqueSpeakers = [...new Set(script.map((turn) => turn.speaker))]
    return uniqueSpeakers.reduce<Record<string, number>>(
      (acc, speaker, index) => {
        acc[speaker] = index
        return acc
      },
      {},
    )
  }, [script])

  // 現在再生中のスクリプト行を特定
  const currentScriptIndex = useMemo(() => {
    if (!currentTime || !script.some((turn) => turn.timestamp !== undefined))
      return -1

    let index = -1
    for (let i = 0; i < script.length; i++) {
      const turn = script[i]
      if (
        turn &&
        turn.timestamp !== undefined &&
        turn.timestamp <= currentTime
      ) {
        index = i
      } else {
        break
      }
    }
    return index
  }, [currentTime, script])

  // 現在の行にスクロール
  useEffect(() => {
    if (currentScriptIndex >= 0 && scrollAreaRef.current) {
      const element = scrollAreaRef.current.querySelector(
        `[data-script-index="${currentScriptIndex}"]`,
      )
      element?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [currentScriptIndex])

  const handleScriptClick = (index: number) => {
    const turn = script[index]
    if (turn?.timestamp !== undefined && onTimeSeek) {
      onTimeSeek(turn.timestamp)
    }
  }

  const formatTime = (seconds?: number) => {
    if (!seconds) return ''
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div
      role="region"
      aria-label={t('podcast.script')}
      className="bg-card/50 rounded-lg border backdrop-blur-sm"
    >
      <div className="border-b px-4 py-3">
        <h3
          className="text-foreground text-sm font-medium"
          id="podcast-script-title"
        >
          {t('podcast.script')}
        </h3>
      </div>
      <div
        className="max-h-[50vh] overflow-y-auto"
        aria-labelledby="podcast-script-title"
        tabIndex={0}
        ref={scrollAreaRef}
      >
        <div className="p-4">
          {script.map((turn, index) => {
            const isCurrentlyPlaying = index === currentScriptIndex
            const speakerIndex = speakerStyles[turn.speaker] || 0

            return (
              <div
                key={index}
                data-script-index={index}
                className={cn(
                  'group border-b py-4 first:pt-0 last:border-0',
                  turn.timestamp !== undefined &&
                    'hover:bg-accent/5 -mx-4 cursor-pointer px-4 transition-colors',
                  isCurrentlyPlaying && 'bg-accent/10 -mx-4 px-4',
                )}
                role="listitem"
                aria-label={`${turn.speaker}: ${turn.text}`}
                onClick={() => handleScriptClick(index)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <Avatar className="h-6 w-6">
                        <AvatarFallback
                          className={cn(
                            'text-xs',
                            turn.speaker.toLowerCase().includes('host') ||
                              turn.speaker.includes('ホスト')
                              ? 'bg-primary text-primary-foreground'
                              : 'bg-muted text-muted-foreground',
                          )}
                        >
                          <User className="h-3 w-3" />
                        </AvatarFallback>
                      </Avatar>
                      <span
                        className={cn(
                          'text-xs font-medium',
                          speakerIndex === 0
                            ? 'text-primary'
                            : 'text-muted-foreground',
                        )}
                      >
                        {turn.speaker}
                      </span>
                      {turn.timestamp !== undefined && (
                        <span className="text-muted-foreground text-xs">
                          {formatTime(turn.timestamp)}
                        </span>
                      )}
                    </div>
                    <p className="text-foreground text-sm leading-relaxed">
                      {turn.text}
                    </p>
                  </div>
                </div>
                {isCurrentlyPlaying && (
                  <div className="bg-primary absolute left-0 top-1/2 h-12 w-0.5 -translate-y-1/2" />
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export const PodcastScript = memo(PodcastScriptComponent)
