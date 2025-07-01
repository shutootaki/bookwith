'use client'

import { AnimatePresence, motion } from 'framer-motion'
import { useAtomValue } from 'jotai'
import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'

import { isGlobalLoadingAtom, primaryTaskAtom } from '../../../store/loading'
import { CircularProgress } from '../spinner'

export function GlobalLoadingOverlay() {
  const isGlobalLoading = useAtomValue(isGlobalLoadingAtom)
  const primaryTask = useAtomValue(primaryTaskAtom)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  return (
    <>
      {createPortal(
        <AnimatePresence>
          {isGlobalLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 z-[9999] flex items-center justify-center bg-gradient-to-br from-black/60 via-black/50 to-black/60 backdrop-blur-md"
              onClick={(e) => e.stopPropagation()}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="min-w-[280px] max-w-[420px] rounded-2xl bg-white/95 p-8 shadow-2xl ring-1 ring-gray-200/50 backdrop-blur-sm dark:bg-gray-900/95 dark:ring-gray-700/50"
              >
                <div className="flex flex-col items-center space-y-5">
                  <div className="relative">
                    <div className="absolute inset-0 animate-ping rounded-full bg-blue-400 opacity-20" />
                    <CircularProgress
                      size="lg"
                      thickness="normal"
                      className="text-blue-500"
                    />
                  </div>

                  {primaryTask?.message && (
                    <p className="text-center text-base font-medium text-gray-700 dark:text-gray-300">
                      {primaryTask.message}
                    </p>
                  )}

                  {primaryTask?.progress && (
                    <div className="w-full">
                      <div className="relative h-3 w-full overflow-hidden rounded-full bg-gray-200 shadow-inner dark:bg-gray-700">
                        <motion.div
                          className="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-600 shadow-sm"
                          initial={{ width: 0 }}
                          animate={{
                            width: `${
                              (primaryTask.progress.current /
                                primaryTask.progress.total) *
                              100
                            }%`,
                          }}
                          transition={{ duration: 0.3, ease: 'easeOut' }}
                        />
                      </div>
                      <div className="mt-2 flex items-center justify-between text-xs">
                        <span className="text-gray-500 dark:text-gray-400">
                          進捗:{' '}
                          {Math.round(
                            (primaryTask.progress.current /
                              primaryTask.progress.total) *
                              100,
                          )}
                          %
                        </span>
                        <span className="text-gray-500 dark:text-gray-400">
                          {primaryTask.progress.current} /{' '}
                          {primaryTask.progress.total}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>,
        document.body,
      )}
    </>
  )
}
