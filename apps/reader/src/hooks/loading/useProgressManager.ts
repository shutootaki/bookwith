import { useSetAtom } from 'jotai'
import { useCallback } from 'react'

import { updateTaskAtom, LoadingTask } from '../../store/loading'

/**
 * プログレス管理を担当するフック
 */
export function useProgressManager(getCurrentTaskId: () => string | null) {
  const updateTask = useSetAtom(updateTaskAtom)

  const updateProgress = useCallback(
    (current: number, total: number) => {
      const currentTaskId = getCurrentTaskId()
      if (!currentTaskId) return

      updateTask({
        id: currentTaskId,
        updates: {
          progress: { current, total },
        },
      })
    },
    [updateTask, getCurrentTaskId],
  )

  const updateSubTasks = useCallback(
    (subTasksUpdate: Partial<LoadingTask['subTasks']>) => {
      const currentTaskId = getCurrentTaskId()
      if (!currentTaskId) return

      updateTask({
        id: currentTaskId,
        updates: {
          subTasks: subTasksUpdate as LoadingTask['subTasks'],
        },
      })
    },
    [updateTask, getCurrentTaskId],
  )

  return {
    updateProgress,
    updateSubTasks,
  }
}
