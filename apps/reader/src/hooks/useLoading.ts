import { useAtom, useAtomValue, useSetAtom } from 'jotai'
import { useCallback, useRef } from 'react'

import {
  LoadingTask,
  addTaskAtom,
  isGlobalLoadingAtom,
  loadingTasksAtom,
  removeTaskAtom,
  updateTaskAtom,
} from '../store/loading'

export interface UseLoadingOptions {
  message?: string
  type?: 'global' | 'local'
  showProgress?: boolean
  icon?: string
  /** ユーザーがキャンセルできるタスクか */
  canCancel?: boolean
}

export function useLoading(options?: UseLoadingOptions) {
  const [tasks] = useAtom(loadingTasksAtom)
  const isGlobalLoading = useAtomValue(isGlobalLoadingAtom)
  const addTask = useSetAtom(addTaskAtom)
  const updateTask = useSetAtom(updateTaskAtom)
  const removeTask = useSetAtom(removeTaskAtom)

  // 現在のタスクIDを追跡
  const currentTaskIdRef = useRef<string | null>(null)

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
      currentTaskIdRef.current = id

      return id
    },
    [addTask, options],
  )

  const updateProgress = useCallback(
    (current: number, total: number) => {
      if (!currentTaskIdRef.current) return

      updateTask({
        id: currentTaskIdRef.current,
        updates: {
          progress: { current, total },
        },
      })
    },
    [updateTask],
  )

  const updateSubTasks = useCallback(
    (subTasksUpdate: Partial<LoadingTask['subTasks']>) => {
      if (!currentTaskIdRef.current) return

      updateTask({
        id: currentTaskIdRef.current,
        updates: {
          subTasks: subTasksUpdate as LoadingTask['subTasks'],
        },
      })
    },
    [updateTask],
  )

  const stopLoading = useCallback(
    (taskId?: string) => {
      const id = taskId || currentTaskIdRef.current

      if (id) {
        removeTask(id)

        if (id === currentTaskIdRef.current) {
          currentTaskIdRef.current = null
        }
      }
    },
    [removeTask],
  )

  // このフックインスタンスがローディング中かどうか
  const isLoading = currentTaskIdRef.current
    ? tasks.has(currentTaskIdRef.current)
    : false

  return {
    startLoading,
    updateProgress,
    updateSubTasks,
    stopLoading,
    isLoading,
    isGlobalLoading,
  }
}
