import { motion } from 'framer-motion'
import React, { memo, useMemo } from 'react'

import { useTranslation } from '../../hooks/useTranslation'
import { Card } from '../ui/card'
import { ScrollArea } from '../ui/scroll-area'

interface ScriptTurn {
  speaker: string
  text: string
}

interface PodcastScriptProps {
  script: ScriptTurn[]
  className?: string
}

const PodcastScriptComponent: React.FC<PodcastScriptProps> = ({
  script,
  className = '',
}) => {
  const t = useTranslation()

  const speakerColors = useMemo(() => {
    const uniqueSpeakers = [...new Set(script.map((turn) => turn.speaker))]
    const colors = ['bg-primary', 'bg-secondary', 'bg-accent']

    return uniqueSpeakers.reduce((acc, speaker, index) => {
      acc[speaker] = colors[index % colors.length] || 'bg-primary'
      return acc
    }, {} as Record<string, string>)
  }, [script])

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.3 }}
      className={className}
      role="region"
      aria-label={t('podcast.script')}
    >
      <Card className="p-6">
        <h3
          className="text-foreground mb-4 text-lg font-semibold"
          id="podcast-script-title"
        >
          {t('podcast.script')}
        </h3>
        <ScrollArea
          className="h-96"
          aria-labelledby="podcast-script-title"
          tabIndex={0}
        >
          <div
            className="space-y-4"
            role="list"
            aria-label={t('podcast.script_dialogue')}
          >
            {script.map((turn, index) => (
              <div
                key={index}
                className="flex space-x-3"
                role="listitem"
                aria-label={`${turn.speaker}: ${turn.text}`}
              >
                <div className="flex-shrink-0">
                  <span
                    className={`${
                      speakerColors[turn.speaker] || 'bg-primary'
                    } text-primary-foreground inline-flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium`}
                    aria-hidden="true"
                  >
                    {turn.speaker}
                  </span>
                </div>
                <div className="flex-1">
                  <span className="sr-only">{turn.speaker} says:</span>
                  <p className="text-foreground text-sm leading-relaxed">
                    {turn.text}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </Card>
    </motion.div>
  )
}

export const PodcastScript = memo(PodcastScriptComponent)

PodcastScript.displayName = 'PodcastScript'
