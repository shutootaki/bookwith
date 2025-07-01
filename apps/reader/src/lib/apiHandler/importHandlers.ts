import { v4 as uuidv4 } from 'uuid'

import { fileToEpub, indexEpub } from '../../epub'
import { fileToBase64, toDataUrl } from '../../fileUtils'
import { mapExtToMimes } from '../../mime'
import { TEST_USER_ID } from '../../pages/_app'
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

    await indexEpub(file, TEST_USER_ID, bookData.id)

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
  const newBooks: BookDetail[] = []

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

  const existingBooks = await fetchAllBooks()

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

        let book = existingBooks?.find((b) => b.name === file.name)

        setImportProgress?.({
          total: fileArray.length,
          completed: completedCount,
          importing: true,
          success: successCount,
          failed: failedCount,
          currentFile: {
            name: file.name,
            progress: 40,
            index: i,
          },
        })

        const trackingSetLoading = (id: string | undefined) => {
          setLoading?.(id)

          if (id) {
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
