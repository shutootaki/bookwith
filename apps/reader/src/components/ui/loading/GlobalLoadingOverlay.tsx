'use client'

import { AnimatePresence, motion } from 'framer-motion'
import { useAtomValue, useSetAtom } from 'jotai'
import { useEffect, useMemo, useState, useId } from 'react'
import { createPortal } from 'react-dom'

import {
  isGlobalLoadingAtom,
  primaryTaskAtom,
  removeTaskAtom,
} from '../../../store/loading'
import { CircularProgress } from '../spinner'

export function GlobalLoadingOverlay() {
  const isGlobalLoading = useAtomValue(isGlobalLoadingAtom)
  const primaryTask = useAtomValue(primaryTaskAtom)
  const removeTask = useSetAtom(removeTaskAtom)
  const [mounted, setMounted] = useState(false)

  // アクセシビリティ用の一意 ID
  const titleId = useId()
  const descId = useId()

  useEffect(() => {
    setMounted(true)
  }, [])

  // 進捗率計算
  const percent = useMemo(() => {
    if (!primaryTask?.progress) return 0
    const { current, total } = primaryTask.progress
    if (total === 0) return 0
    return (current / total) * 100
  }, [primaryTask?.progress])

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
              transition={{ duration: 0.15 }}
              className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
              onClick={(e) => e.stopPropagation()}
              role="dialog"
              aria-modal="true"
              aria-labelledby={titleId}
              aria-describedby={descId}
            >
              <motion.div
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: 10, opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="mx-4 min-w-[240px] max-w-[360px] rounded-lg bg-white p-6 shadow-lg dark:bg-gray-900"
              >
                <div
                  className="flex flex-col items-center space-y-4"
                  tabIndex={-1}
                  aria-busy="true"
                >
                  {/* スクリーンリーダー向けタイトル */}
                  <h2 id={titleId} className="sr-only">
                    読み込み中
                  </h2>

                  <CircularProgress
                    size="md"
                    thickness="normal"
                    className="text-blue-500"
                    aria-label="読み込み中"
                  />

                  {primaryTask?.message && (
                    <p className="text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                      {primaryTask.message}
                    </p>
                  )}

                  {primaryTask?.subTasks && (
                    <div className="space-y-1 text-center">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {primaryTask.subTasks.filesCompleted}/
                        {primaryTask.subTasks.filesTotal}冊をインポート中
                      </p>
                      {primaryTask.subTasks.currentFileName && (
                        <p
                          className="max-w-[300px] truncate text-xs text-gray-500 dark:text-gray-400"
                          title={primaryTask.subTasks.currentFileName}
                        >
                          {primaryTask.subTasks.currentFileName}
                        </p>
                      )}
                    </div>
                  )}

                  {primaryTask?.progress && (
                    <div className="w-full">
                      <div
                        className="relative h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700"
                        role="progressbar"
                        aria-valuemin={0}
                        aria-valuemax={primaryTask.progress.total}
                        aria-valuenow={primaryTask.progress.current}
                      >
                        <motion.div
                          className="h-full rounded-full bg-blue-500"
                          initial={{ width: 0 }}
                          animate={{
                            width: `${
                              (primaryTask.progress.current /
                                primaryTask.progress.total) *
                              100
                            }%`,
                          }}
                          transition={{ duration: 0.2, ease: 'easeOut' }}
                        />
                      </div>
                      <div className="mt-1.5 flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
                        <span>{Math.round(percent)}%</span>
                        <span>
                          {primaryTask.progress.current} /{' '}
                          {primaryTask.progress.total}
                        </span>
                      </div>
                    </div>
                  )}

                  <div className="mt-2 flex w-full justify-end space-x-2">
                    {primaryTask?.canCancel && (
                      <button
                        onClick={() =>
                          primaryTask && removeTask(primaryTask.id)
                        }
                        className="rounded-md bg-red-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2"
                      >
                        キャンセル
                      </button>
                    )}
                  </div>
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

// Helpers（現在は未使用）
