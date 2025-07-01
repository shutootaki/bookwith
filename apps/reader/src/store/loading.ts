import { atom } from 'jotai'

// Types
export interface LoadingTask {
  id: string // タスクの一意識別子
  message?: string // 表示メッセージ
  progress?: {
    // プログレス情報（オプション）
    current: number
    total: number
  }
  type: 'global' | 'local' // ローディングのスコープ
  icon?: string // アイコン（オプション）
}

// Atoms
// タスクを管理するアトム
export const loadingTasksAtom = atom<Map<string, LoadingTask>>(new Map())

// 派生アトム（計算プロパティ）
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

// Actions（アトムを操作する関数）
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
      tasks.set(id, { ...existingTask, ...updates })
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
