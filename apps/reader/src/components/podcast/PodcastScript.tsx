import { motion } from 'framer-motion'
import React from 'react'

import { useTranslation } from '../../hooks/useTranslation'
import { Card } from '../ui/card'
import { ScrollArea } from '../ui/scroll-area'

interface ScriptTurn {
  speaker: string
  text: string
}

interface PodcastScriptProps {
  script: ScriptTurn[]
}

export const PodcastScript: React.FC<PodcastScriptProps> = ({ script }) => {
  const t = useTranslation()

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="p-6">
        <h3 className="text-foreground mb-4 text-lg font-semibold">
          {t('podcast.script')}
        </h3>
        <ScrollArea className="h-96">
          <div className="space-y-4">
            {script.map((turn, index) => (
              <div key={index} className="flex space-x-3">
                <div className="flex-shrink-0">
                  <span className="bg-primary text-primary-foreground inline-flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium">
                    {turn.speaker}
                  </span>
                </div>
                <div className="flex-1">
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
