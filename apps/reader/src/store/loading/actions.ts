import { atom } from 'jotai'

import { LoadingTask, LoadingTaskWithUpdates } from '../../types/loading'

import { loadingTasksAtom } from './atoms'

/**
 * Write-only atom for adding a new loading task
 */
export const addTaskAtom = atom(null, (get, set, task: LoadingTask) => {
  const tasks = new Map(get(loadingTasksAtom))
  tasks.set(task.id, task)
  set(loadingTasksAtom, tasks)
})

/**
 * Write-only atom for updating an existing loading task
 */
export const updateTaskAtom = atom(
  null,
  (get, set, { id, updates }: LoadingTaskWithUpdates) => {
    const tasks = new Map(get(loadingTasksAtom))
    const existingTask = tasks.get(id)
    if (existingTask) {
      const updatedTask = { ...existingTask }

      // Handle nested subTasks update
      if (updates.subTasks && existingTask.subTasks) {
        updatedTask.subTasks = {
          ...existingTask.subTasks,
          ...updates.subTasks,
        }

        const { subTasks, ...otherUpdates } = updates
        Object.assign(updatedTask, otherUpdates)
      } else {
        Object.assign(updatedTask, updates)
      }

      tasks.set(id, updatedTask)
      set(loadingTasksAtom, tasks)
    }
  },
)

/**
 * Write-only atom for removing a loading task
 */
export const removeTaskAtom = atom(null, (get, set, id: string) => {
  const tasks = new Map(get(loadingTasksAtom))
  tasks.delete(id)
  set(loadingTasksAtom, tasks)
})

/**
 * Write-only atom for clearing all loading tasks
 */
export const clearAllTasksAtom = atom(null, (get, set) => {
  set(loadingTasksAtom, new Map())
})

/**
 * Write-only atom for removing all tasks of a specific type
 */
export const clearTasksByTypeAtom = atom(
  null,
  (get, set, type: 'global' | 'local') => {
    const tasks = new Map(get(loadingTasksAtom))
    const filteredTasks = new Map(
      Array.from(tasks.entries()).filter(([, task]) => task.type !== type),
    )
    set(loadingTasksAtom, filteredTasks)
  },
)
