import React, { useEffect, useRef, useState } from 'react'
import { Progress } from './ui/progress'
import { CircularProgress } from './ui/spinner'
import { useTranslation } from '../hooks'

export interface ImportProgressState {
  total: number
  completed: number
  importing: boolean
  success?: number
  failed?: number
  currentFile?: {
    name: string
    progress: number // 0-100の範囲
    index: number
  }
}

interface ImportProgressProps {
  progress: ImportProgressState
}

// アニメーション付き進捗表示のためのカスタムフック
export function useAnimatedProgress(currentFile?: {
  name: string
  progress: number
  index: number
}) {
  const [animatedProgress, setAnimatedProgress] = useState<{
    value: number
    target: number
    fileName: string | null
  }>({ value: 0, target: 0, fileName: null })

  const progressTimerRef = useRef<NodeJS.Timeout | null>(null)

  // 現在のファイルの進捗が更新されたときに目標値を更新
  useEffect(() => {
    if (currentFile) {
      // 新しいファイルの処理が始まった場合
      if (animatedProgress.fileName !== currentFile.name) {
        setAnimatedProgress({
          value: 0,
          target: currentFile.progress,
          fileName: currentFile.name,
        })
      }
      // 同じファイルで進捗目標が更新された場合
      else if (animatedProgress.target !== currentFile.progress) {
        setAnimatedProgress((prev) => ({
          ...prev,
          target: currentFile.progress,
        }))
      }
    } else {
      // インポート終了時
      setAnimatedProgress({ value: 0, target: 0, fileName: null })
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current)
        progressTimerRef.current = null
      }
    }
  }, [currentFile, animatedProgress.fileName, animatedProgress.target])

  // 1%ずつ進捗を更新するアニメーション
  useEffect(() => {
    // すでに目標に到達している場合はタイマーをクリア
    if (animatedProgress.value >= animatedProgress.target) {
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current)
        progressTimerRef.current = null
      }
      return
    }

    // アニメーションタイマーをセット
    if (!progressTimerRef.current && animatedProgress.fileName) {
      progressTimerRef.current = setInterval(() => {
        setAnimatedProgress((prev) => {
          // 目標に到達した場合はタイマーをクリア
          if (prev.value >= prev.target) {
            if (progressTimerRef.current) {
              clearInterval(progressTimerRef.current)
              progressTimerRef.current = null
            }
            return prev
          }

          // 1%ずつ増加（より速く目標に近づくよう調整可能）
          return {
            ...prev,
            value: Math.min(prev.value + 1, prev.target),
          }
        })
      }, 50) // 50ミリ秒ごとに更新（調整可能）
    }

    // コンポーネントのアンマウント時にタイマーをクリア
    return () => {
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current)
        progressTimerRef.current = null
      }
    }
  }, [animatedProgress])

  return animatedProgress
}

// 個別ファイルの進捗表示コンポーネント
const FileProgressItem: React.FC<{
  fileName: string
  progress: number
}> = ({ fileName, progress }) => {
  const t = useTranslation('import')

  return (
    <div className="mt-4 border-t border-gray-100 pt-3 dark:border-gray-800">
      <div className="flex items-center justify-between">
        <div className="flex-1 truncate text-sm font-medium">
          {t('processing')}: {fileName}
        </div>
        <div className="text-muted-foreground text-xs">
          {Math.round(progress)}%
        </div>
      </div>
      <Progress
        value={progress}
        className="mt-2 h-1"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progress)}
        aria-valuetext={`${fileName}${t('processing_aria')}: ${Math.round(
          progress,
        )}%`}
      />
      <div className="mt-2 flex flex-wrap gap-2">
        {progress < 30 && (
          <div className="text-muted-foreground text-xs">
            {t('analyzing_file')}
          </div>
        )}
        {progress >= 30 && progress < 60 && (
          <div className="text-muted-foreground text-xs">
            {t('processing_metadata')}
          </div>
        )}
        {progress >= 60 && progress < 90 && (
          <div className="text-muted-foreground text-xs">
            {t('processing_content')}
          </div>
        )}
        {progress >= 90 && (
          <div className="text-muted-foreground text-xs">{t('saving')}</div>
        )}
      </div>
    </div>
  )
}

// メインのインポート進捗表示コンポーネント
const ImportProgress: React.FC<ImportProgressProps> = ({ progress }) => {
  const animatedProgress = useAnimatedProgress(progress.currentFile)
  const t = useTranslation('import')

  if (!progress.importing) return null

  return (
    <div
      className="dark:bg-gray-950 mb-4 rounded-lg border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <CircularProgress className="text-primary h-6 w-6" />
          <div className="font-medium">
            {t('importing_books', {
              completed: progress.completed,
              total: progress.total,
            })}
          </div>
        </div>
        <div className="text-muted-foreground text-sm">
          {Math.round((progress.completed / progress.total) * 100)}%
        </div>
      </div>
      <Progress
        value={(progress.completed / progress.total) * 100}
        className="mt-3 h-2"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round((progress.completed / progress.total) * 100)}
        aria-valuetext={`${progress.completed}/${progress.total} ${t(
          'files_processed',
        )} (${Math.round((progress.completed / progress.total) * 100)}%)`}
      />

      {/* 現在処理中のファイル情報と詳細な進行状況 */}
      {progress.currentFile && animatedProgress.fileName && (
        <FileProgressItem
          fileName={progress.currentFile.name}
          progress={animatedProgress.value}
        />
      )}

      <p className="text-muted-foreground mt-2 text-xs">
        {progress.success !== undefined && progress.failed !== undefined
          ? t('import_status', {
              success: progress.success,
              failed: progress.failed,
            })
          : t('please_wait')}
      </p>
    </div>
  )
}

export default ImportProgress
