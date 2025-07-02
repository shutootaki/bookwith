import { atom } from 'jotai'

export interface LoadingTask {
  id: string
  message?: string
  startTime?: number
  progress?: {
    current: number
    total: number
  }
  type: 'global' | 'local'
  canCancel?: boolean
  icon?: string
  subTasks?: {
    currentFileName?: string
    filesCompleted: number
    filesTotal: number
  }
}

export const loadingTasksAtom = atom<Map<string, LoadingTask>>(new Map())

export const isGlobalLoadingAtom = atom((get) => {
  const tasks = get(loadingTasksAtom)
  return Array.from(tasks.values()).some((task) => task.type === 'global')
})

export const activeTasksCountAtom = atom((get) => get(loadingTasksAtom).size)

export const primaryTaskAtom = atom<LoadingTask | null>((get) => {
  const tasks = get(loadingTasksAtom)
  const globalTasks = Array.from(tasks.values()).filter(
    (task) => task.type === 'global',
  )
  return globalTasks[0] || null
})

export const addTaskAtom = atom(null, (get, set, task: LoadingTask) => {
  const tasks = new Map(get(loadingTasksAtom))
  tasks.set(task.id, task)
  set(loadingTasksAtom, tasks)
})

export const updateTaskAtom = atom(
  null,
  (
    get,
    set,
    { id, updates }: { id: string; updates: Partial<LoadingTask> },
  ) => {
    const tasks = new Map(get(loadingTasksAtom))
    const existingTask = tasks.get(id)
    if (existingTask) {
      const updatedTask = { ...existingTask }

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

export const removeTaskAtom = atom(null, (get, set, id: string) => {
  const tasks = new Map(get(loadingTasksAtom))
  tasks.delete(id)
  set(loadingTasksAtom, tasks)
})

export const clearAllTasksAtom = atom(null, (get, set) => {
  set(loadingTasksAtom, new Map())
})
