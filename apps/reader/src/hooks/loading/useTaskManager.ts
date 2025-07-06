import { useSetAtom } from 'jotai'
import { useCallback } from 'react'

import { addTaskAtom, removeTaskAtom, LoadingTask } from '../../store/loading'

export interface UseTaskManagerOptions {
  message?: string
  type?: 'global' | 'local'
  showProgress?: boolean
  icon?: string
  /** ユーザーがキャンセルできるタスクか */
  canCancel?: boolean
}

/**
 * タスクの作成・削除を管理するフック
 */
export function useTaskManager(
  setCurrentTaskId: (id: string | null) => void,
  getCurrentTaskId: () => string | null,
  options?: UseTaskManagerOptions,
) {
  const addTask = useSetAtom(addTaskAtom)
  const removeTask = useSetAtom(removeTaskAtom)

  const startLoading = useCallback(
    (taskId?: string, customOptions?: { filesTotal?: number }) => {
      const id =
        taskId ||
        `task-${Date.now()}-${Math.random().toString(36).substring(7)}`

      const task: LoadingTask = {
        id,
        message: options?.message,
        type: options?.type || 'global',
        icon: options?.icon,
        startTime: Date.now(),
        canCancel: options?.canCancel,
      }

      if (options?.showProgress) {
        task.progress = {
          current: 0,
          total: 100,
        }
      }

      if (customOptions?.filesTotal) {
        task.subTasks = {
          filesCompleted: 0,
          filesTotal: customOptions.filesTotal,
        }
      }

      addTask(task)
      setCurrentTaskId(id)

      return id
    },
    [addTask, options, setCurrentTaskId],
  )

  const stopLoading = useCallback(
    (taskId?: string) => {
      const currentTaskId = getCurrentTaskId()
      const id = taskId || currentTaskId

      if (id) {
        removeTask(id)

        if (id === currentTaskId) {
          setCurrentTaskId(null)
        }
      }
    },
    [removeTask, getCurrentTaskId, setCurrentTaskId],
  )

  return {
    startLoading,
    stopLoading,
  }
}
