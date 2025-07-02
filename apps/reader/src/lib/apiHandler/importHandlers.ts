import { v4 as uuidv4 } from 'uuid'

import { TEST_USER_ID } from '../../pages/_app'
import { fileToEpub, indexEpub } from '../../utils/epub'
import { fileToBase64, toDataUrl } from '../../utils/fileUtils'
import { mapExtToMimes } from '../../utils/mime'
import { components } from '../openapi-schema/schema'

import { createBook, fetchAllBooks } from './bookApiHandler'

type BookDetail = components['schemas']['BookDetail']

export async function addBook(
  file: File,
  setLoading?: (id: string | undefined) => void,
): Promise<BookDetail | null> {
  const epub = await fileToEpub(file)
  const metadata = await epub.loaded.metadata

  const tempBookId = uuidv4()
  setLoading?.(tempBookId)

  try {
    const coverUrl = await epub.coverUrl()
    let coverDataUrl = null
    if (coverUrl) {
      coverDataUrl = await toDataUrl(coverUrl)
    }

    const bookRequest: components['schemas']['BookCreateRequest'] = {
      fileData: await fileToBase64(file),
      fileName: file.name,
      userId: TEST_USER_ID,
      bookId: tempBookId,
      bookName: file.name || `${metadata.title}.epub`,
      bookMetadata: JSON.stringify(metadata),
      coverImage: coverDataUrl || null,
    }

    const bookData = await createBook(bookRequest)

    if (!bookData) {
      console.error('APIへの書籍登録に失敗しました')
      setLoading?.(undefined)
      return null
    }

    await indexEpub(file, TEST_USER_ID)

    setLoading?.(undefined)
    return bookData
  } catch (error) {
    console.error('書籍の登録中にエラーが発生しました:', error)
    setLoading?.(undefined)
    return null
  }
}

export async function fetchBook(
  url: string,
  setLoading?: (id: string | undefined) => void,
): Promise<BookDetail | null> {
  const filename = decodeURIComponent(/\/([^/]*\.epub)$/i.exec(url)?.[1] ?? '')

  const existingBooks = await fetchAllBooks()
  const book = existingBooks?.find((b) => b.name === filename)

  if (book) {
    return book
  }

  try {
    const res = await fetch(url)
    if (!res.ok) {
      throw new Error(`Failed to fetch book from URL: ${res.statusText}`)
    }
    const blob = await res.blob()
    return await addBook(new File([blob], filename), setLoading)
  } catch (error) {
    console.error(`Error fetching or adding book from URL ${url}:`, error)
    return null
  }
}

export async function handleFiles(
  files: Iterable<File>,
  setLoading?: (id: string | undefined) => void,
  updateProgress?: (current: number, total: number) => void,
  updateSubTasks?: (subTasksUpdate: any) => void,
) {
  const fileArray = Array.from(files)
  const newBooks: BookDetail[] = []

  // 初期進捗を設定
  updateProgress?.(0, fileArray.length * 100)

  let completedCount = 0
  let successCount = 0
  let failedCount = 0

  const existingBooks = await fetchAllBooks()

  try {
    for (let i = 0; i < fileArray.length; i++) {
      const file = fileArray[i]
      if (!file) continue
      try {
        // ファイル名を更新
        updateSubTasks?.({
          currentFileName: file.name,
        })
        
        // ファイルごとの進捗を計算
        const fileProgress = i * 100 + 0 // 各ファイルは0-100%の進捗
        updateProgress?.(fileProgress, fileArray.length * 100)

        if (mapExtToMimes['.zip'].includes(file.type)) {
          // ZIPファイルの進捗: 30%
          updateProgress?.(i * 100 + 30, fileArray.length * 100)

          // ZIPファイルの完了: 100%
          updateProgress?.(i * 100 + 100, fileArray.length * 100)

          completedCount++
          continue
        }

        if (!mapExtToMimes['.epub'].includes(file.type)) {
          console.error(`Unsupported file type: ${file.type}`)

          // サポートされていないファイル形式: 100%
          updateProgress?.(i * 100 + 100, fileArray.length * 100)

          completedCount++
          failedCount++
          continue
        }

        // ePubファイルの読み込み: 20%
        updateProgress?.(i * 100 + 20, fileArray.length * 100)

        let book = existingBooks?.find((b) => b.name === file.name)

        // 既存ファイルのチェック: 40%
        updateProgress?.(i * 100 + 40, fileArray.length * 100)

        const trackingSetLoading = (id: string | undefined) => {
          setLoading?.(id)

          if (id) {
            // サーバーにアップロード中: 60%
            updateProgress?.(i * 100 + 60, fileArray.length * 100)
          } else {
            // メタデータ処理: 90%
            updateProgress?.(i * 100 + 90, fileArray.length * 100)
          }
        }

        if (!book) {
          const addedBook = await addBook(file, trackingSetLoading)
          if (addedBook) {
            book = addedBook
            existingBooks.push(addedBook)
          }
        }

        if (book) {
          newBooks.push(book)
          successCount++
        } else {
          failedCount++
        }

        // ファイルの完了: 100%
        completedCount++
        updateProgress?.(completedCount * 100, fileArray.length * 100)
        updateSubTasks?.({
          filesCompleted: completedCount,
        })
      } catch (error) {
        console.error(`ファイルのインポート中にエラーが発生しました: ${error}`)

        // エラー時も完了として扱う
        completedCount++
        failedCount++
        updateProgress?.(completedCount * 100, fileArray.length * 100)
        updateSubTasks?.({
          filesCompleted: completedCount,
        })
      }
    }
  } finally {
    // 最終的に100%に設定
    updateProgress?.(fileArray.length * 100, fileArray.length * 100)
    updateSubTasks?.({
      currentFileName: undefined,
      filesCompleted: completedCount,
    })
  }

  return { newBooks, success: successCount, failed: failedCount }
}
