import { atom } from 'jotai'

import { LoadingTaskMap } from '../../types/loading'

/**
 * Core atom that holds all loading tasks
 */
export const loadingTasksAtom = atom<LoadingTaskMap>(new Map())
