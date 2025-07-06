/**
 * Loading task types and interfaces
 */

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

export type LoadingTaskUpdate = Partial<LoadingTask>

export interface LoadingTaskWithUpdates {
  id: string
  updates: LoadingTaskUpdate
}

export type LoadingTaskType = 'global' | 'local'

export type LoadingTaskMap = Map<string, LoadingTask>
