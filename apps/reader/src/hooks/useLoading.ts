import { useRef } from 'react'

import {
  useLoadingState,
  useProgressManager,
  useTaskManager,
  UseTaskManagerOptions,
} from './loading'

export type UseLoadingOptions = UseTaskManagerOptions

/**
 * ローディング状態を管理するための統合フック
 * 後方互換性のために従来のAPIを維持します
 */
export function useLoading(options?: UseLoadingOptions) {
  const currentTaskIdRef = useRef<string | null>(null)

  const getCurrentTaskId = () => currentTaskIdRef.current
  const setCurrentTaskId = (id: string | null) => {
    currentTaskIdRef.current = id
  }

  const { isLoading, isGlobalLoading } = useLoadingState(getCurrentTaskId)
  const { updateProgress, updateSubTasks } =
    useProgressManager(getCurrentTaskId)
  const { startLoading, stopLoading } = useTaskManager(
    setCurrentTaskId,
    getCurrentTaskId,
    options,
  )

  return {
    startLoading,
    updateProgress,
    updateSubTasks,
    stopLoading,
    isLoading,
    isGlobalLoading,
  }
}
