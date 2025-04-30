import { v4 as uuidv4 } from 'uuid'

import { fileToEpub, indexEpub } from '../../epub'
import { fileToBase64, toDataUrl } from '../../fileUtils'
import { mapExtToMimes } from '../../mime'
import { TEST_USER_ID } from '../../pages/_app'
import { components } from '../openapi-schema/schema'

import { createBook, fetchAllBooks } from './bookApiHandler'

export async function addBook(
  file: File,
  setLoading?: (id: string | undefined) => void,
) {
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
) {
  const filename = decodeURIComponent(/\/([^/]*\.epub)$/i.exec(url)?.[1] ?? '')

  const existingBooks = await fetchAllBooks()
  const book = existingBooks?.find((b) => b.name === filename)

  return (
    book ??
    fetch(url)
      .then((res) => res.blob())
      .then((blob) => addBook(new File([blob], filename), setLoading))
  )
}

export async function handleFiles(
  files: Iterable<File>,
  setLoading?: (id: string | undefined) => void,
  setImportProgress?: (status: {
    total: number
    completed: number
    importing: boolean
    success?: number
    failed?: number
    currentFile?: {
      name: string
      progress: number
      index: number
    }
  }) => void,
) {
  const fileArray = Array.from(files)
  const newBooks = []

  setImportProgress?.({
    total: fileArray.length,
    completed: 0,
    importing: true,
    success: 0,
    failed: 0,
  })

  let completedCount = 0
  let successCount = 0
  let failedCount = 0

  try {
    for (let i = 0; i < fileArray.length; i++) {
      const file = fileArray[i]
      if (!file) continue
      try {
        setImportProgress?.({
          total: fileArray.length,
          completed: completedCount,
          importing: true,
          success: successCount,
          failed: failedCount,
          currentFile: {
            name: file.name,
            progress: 0,
            index: i,
          },
        })

        if (mapExtToMimes['.zip'].includes(file.type)) {
          setImportProgress?.({
            total: fileArray.length,
            completed: completedCount,
            importing: true,
            success: successCount,
            failed: failedCount,
            currentFile: {
              name: file.name,
              progress: 30,
              index: i,
            },
          })

          setImportProgress?.({
            total: fileArray.length,
            completed: completedCount,
            importing: true,
            success: successCount,
            failed: failedCount,
            currentFile: {
              name: file.name,
              progress: 100,
              index: i,
            },
          })

          completedCount++
          setImportProgress?.({
            total: fileArray.length,
            completed: completedCount,
            importing: true,
            success: successCount,
            failed: failedCount,
          })
          continue
        }

        if (!mapExtToMimes['.epub'].includes(file.type)) {
          console.error(`Unsupported file type: ${file.type}`)

          setImportProgress?.({
            total: fileArray.length,
            completed: completedCount,
            importing: true,
            success: successCount,
            failed: failedCount,
            currentFile: {
              name: file.name,
              progress: 100,
              index: i,
            },
          })

          completedCount++
          failedCount++
          setImportProgress?.({
            total: fileArray.length,
            completed: completedCount,
            importing: true,
            success: successCount,
            failed: failedCount,
          })
          continue
        }

        // ファイルの処理進行状況を段階的に更新
        setImportProgress?.({
          total: fileArray.length,
          completed: completedCount,
          importing: true,
          success: successCount,
          failed: failedCount,
          currentFile: {
            name: file.name,
            progress: 20,
            index: i,
          },
        })

        const existingBooks = await fetchAllBooks()
        let book = existingBooks?.find((b) => b.name === file.name)

        setImportProgress?.({
          total: fileArray.length,
          completed: completedCount,
          importing: true,
          success: successCount,
          failed: failedCount,
          currentFile: {
            name: file.name,
            progress: 40, // 既存の本をチェック完了
            index: i,
          },
        })

        // 書籍のインポート処理を進捗を報告するラッパー関数
        const trackingSetLoading = (id: string | undefined) => {
          // 既存の処理を維持しつつ、進捗状態も更新
          setLoading?.(id)

          if (id) {
            // idが設定されている場合は処理中
            setImportProgress?.({
              total: fileArray.length,
              completed: completedCount,
              importing: true,
              success: successCount,
              failed: failedCount,
              currentFile: {
                name: file.name,
                progress: 60,
                index: i,
              },
            })
          } else {
            setImportProgress?.({
              total: fileArray.length,
              completed: completedCount,
              importing: true,
              success: successCount,
              failed: failedCount,
              currentFile: {
                name: file.name,
                progress: 90,
                index: i,
              },
            })
          }
        }

        if (!book) {
          book = (await addBook(file, trackingSetLoading)) || undefined
        }

        if (book) {
          newBooks.push(book)
          successCount++
        } else {
          failedCount++
        }

        setImportProgress?.({
          total: fileArray.length,
          completed: completedCount,
          importing: true,
          success: successCount,
          failed: failedCount,
          currentFile: {
            name: file.name,
            progress: 100,
            index: i,
          },
        })

        completedCount++
        setImportProgress?.({
          total: fileArray.length,
          completed: completedCount,
          importing: true,
          success: successCount,
          failed: failedCount,
        })
      } catch (error) {
        console.error(`ファイルのインポート中にエラーが発生しました: ${error}`)

        // エラー発生を通知
        setImportProgress?.({
          total: fileArray.length,
          completed: completedCount,
          importing: true,
          success: successCount,
          failed: failedCount,
          currentFile: {
            name: file.name,
            progress: 100,
            index: i,
          },
        })

        completedCount++
        failedCount++
        setImportProgress?.({
          total: fileArray.length,
          completed: completedCount,
          importing: true,
          success: successCount,
          failed: failedCount,
        })
      }
    }
  } finally {
    setImportProgress?.({
      total: fileArray.length,
      completed: fileArray.length,
      importing: false,
      success: successCount,
      failed: failedCount,
    })
  }

  return { newBooks, success: successCount, failed: failedCount }
}
