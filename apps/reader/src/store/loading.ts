import { atom } from 'jotai'

// Types
export interface LoadingTask {
  id: string // タスクの一意識別子
  message?: string // 表示メッセージ
  /** タスク開始時刻 (epoch ms)。進捗率と組み合わせて ETA/経過時間を計算するため */
  startTime?: number
  progress?: {
    // プログレス情報（オプション）
    current: number
    total: number
  }
  type: 'global' | 'local' // ローディングのスコープ
  /** ユーザーが UI からキャンセル可能かどうか */
  canCancel?: boolean
  icon?: string // アイコン（オプション）
  subTasks?: {
    // 複数ファイルインポート用の詳細情報
    currentFileName?: string // 現在処理中のファイル名
    filesCompleted: number // 完了したファイル数
    filesTotal: number // 総ファイル数
  }
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
      // ネストされたオブジェクトを適切にマージ
      const updatedTask = { ...existingTask }

      // subTasksが更新に含まれている場合、既存のsubTasksとマージ
      if (updates.subTasks && existingTask.subTasks) {
        updatedTask.subTasks = {
          ...existingTask.subTasks,
          ...updates.subTasks,
        }
        // updatesから削除して、後のスプレッドで上書きされないようにする
        const { subTasks, ...otherUpdates } = updates
        Object.assign(updatedTask, otherUpdates)
      } else {
        // subTasksが含まれていない場合は通常通り更新
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
