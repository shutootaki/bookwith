import { LoadingTask } from '../../types/loading'

/**
 * Generate a unique task ID
 */
export const generateTaskId = (prefix = 'task'): string => {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substring(7)}`
}

/**
 * Calculate progress percentage from current/total values
 */
export const calculateProgressPercentage = (
  current: number,
  total: number,
): number => {
  if (total === 0) return 0
  return Math.round((current / total) * 100)
}

/**
 * Check if a task has progress information
 */
export const hasProgress = (task: LoadingTask): boolean => {
  return task.progress !== undefined
}

/**
 * Check if a task has sub-tasks information
 */
export const hasSubTasks = (task: LoadingTask): boolean => {
  return task.subTasks !== undefined
}

/**
 * Get the elapsed time since task start
 */
export const getElapsedTime = (task: LoadingTask): number => {
  if (!task.startTime) return 0
  return Date.now() - task.startTime
}

/**
 * Format elapsed time as human-readable string
 */
export const formatElapsedTime = (elapsedMs: number): string => {
  const seconds = Math.floor(elapsedMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

/**
 * Create a new loading task with default values
 */
export const createLoadingTask = (
  overrides: Partial<LoadingTask> & Pick<LoadingTask, 'id'>,
): LoadingTask => {
  return {
    type: 'global',
    startTime: Date.now(),
    ...overrides,
  }
}
