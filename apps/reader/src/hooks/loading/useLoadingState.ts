import { useAtomValue } from 'jotai'

import { isGlobalLoadingAtom, loadingTasksAtom } from '../../store/loading'

/**
 * 基本的なローディング状態を管理するフック
 */
export function useLoadingState(getCurrentTaskId: () => string | null) {
  const tasks = useAtomValue(loadingTasksAtom)
  const isGlobalLoading = useAtomValue(isGlobalLoadingAtom)

  // このフックインスタンスがローディング中かどうか
  const currentTaskId = getCurrentTaskId()
  const isLoading = currentTaskId ? tasks.has(currentTaskId) : false

  return {
    tasks,
    isGlobalLoading,
    isLoading,
  }
}
