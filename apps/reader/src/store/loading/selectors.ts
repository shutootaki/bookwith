import { atom } from 'jotai'

import { LoadingTask } from '../../types/loading'

import { loadingTasksAtom } from './atoms'

/**
 * Derived atom that checks if any global loading task exists
 */
export const isGlobalLoadingAtom = atom((get) => {
  const tasks = get(loadingTasksAtom)
  return Array.from(tasks.values()).some((task) => task.type === 'global')
})

/**
 * Derived atom that returns the count of active tasks
 */
export const activeTasksCountAtom = atom((get) => get(loadingTasksAtom).size)

/**
 * Derived atom that returns the primary (first global) task
 */
export const primaryTaskAtom = atom<LoadingTask | null>((get) => {
  const tasks = get(loadingTasksAtom)
  const globalTasks = Array.from(tasks.values()).filter(
    (task) => task.type === 'global',
  )
  return globalTasks[0] || null
})

/**
 * Derived atom that returns all global tasks
 */
export const globalTasksAtom = atom((get) => {
  const tasks = get(loadingTasksAtom)
  return Array.from(tasks.values()).filter((task) => task.type === 'global')
})

/**
 * Derived atom that returns all local tasks
 */
export const localTasksAtom = atom((get) => {
  const tasks = get(loadingTasksAtom)
  return Array.from(tasks.values()).filter((task) => task.type === 'local')
})
