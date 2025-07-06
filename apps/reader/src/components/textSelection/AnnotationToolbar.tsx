import clsx from 'clsx'
import React, { RefObject } from 'react'

import { useTranslation } from '../../hooks'
import { BookTab } from '../../models'
import { typeMap, colorMap } from '../../utils/annotation'
import { scale } from '../../utils/platform'
import { keys } from '../../utils/utils'
import { Button } from '../ui/button'

interface AnnotationToolbarProps {
  tab: BookTab
  cfi: string
  text: string
  annotation?: any
  hide: () => void
  annotationSize?: number
  showAnnotations?: boolean
  ref?: RefObject<HTMLTextAreaElement | null>
}

export const AnnotationToolbar: React.FC<AnnotationToolbarProps> = ({
  tab,
  cfi,
  text,
  annotation,
  hide,
  annotationSize = scale(28, 32),
  showAnnotations = true,
  ref,
}) => {
  const t = useTranslation('menu')

  return (
    <>
      {annotation && !showAnnotations && (
        <div className="mb-2">
          <textarea
            ref={ref}
            name="notes"
            defaultValue={annotation?.notes || ''}
            className="focus:border-primary focus:ring-primary h-40 w-72 rounded-lg border-gray-200 focus:ring-1 dark:border-gray-700"
            autoFocus
          />
        </div>
      )}

      {showAnnotations && (
        <div className="space-y-2">
          {keys(typeMap).map((type) => (
            <div key={type} className="flex justify-center gap-2">
              {keys(colorMap).map((color) => (
                <div
                  key={color}
                  style={{
                    [typeMap[type].style]: colorMap[color],
                    width: annotationSize,
                    height: annotationSize,
                    fontSize: scale(16, 20),
                  }}
                  className={clsx(
                    'text-foreground flex cursor-pointer items-center justify-center rounded-md border border-gray-200 shadow-sm transition-transform hover:scale-105 dark:border-gray-700',
                    typeMap[type].class,
                  )}
                  onClick={() => {
                    tab.putAnnotation(
                      type,
                      cfi,
                      color,
                      text,
                      ref?.current?.value,
                    )
                    hide()
                  }}
                >
                  A
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {annotation && !showAnnotations && (
        <div className="mt-2 flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            className="rounded-md border border-gray-200 hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
            onClick={() => {
              tab.removeAnnotation(cfi)
              hide()
            }}
          >
            {t('delete')}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              hide()
            }}
          >
            {t('cancel')}
          </Button>
          <Button
            className="bg-primary hover:bg-primary/90 ml-auto rounded-md shadow-sm transition-colors"
            size="sm"
            onClick={() => {
              tab.putAnnotation(
                annotation?.type ?? 'highlight',
                cfi,
                annotation?.color ?? 'yellow',
                text,
                ref?.current?.value,
              )
              hide()
            }}
          >
            {t(annotation ? 'update' : 'create')}
          </Button>
        </div>
      )}
    </>
  )
}
