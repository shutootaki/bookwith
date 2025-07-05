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
  console.log('metadataだよ', metadata)

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
  updateProgress?: (current: number, total: number) => void,
  updateSubTasks?: (subTasksUpdate: any) => void,
) {
  const fileArray = Array.from(files)
  const newBooks: BookDetail[] = []

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
        updateSubTasks?.({
          currentFileName: file.name,
        })

        const fileProgress = i * 100 + 0
        updateProgress?.(fileProgress, fileArray.length * 100)

        if (mapExtToMimes['.zip'].includes(file.type)) {
          updateProgress?.(i * 100 + 30, fileArray.length * 100)

          updateProgress?.(i * 100 + 100, fileArray.length * 100)

          completedCount++
          continue
        }

        if (!mapExtToMimes['.epub'].includes(file.type)) {
          console.error(`Unsupported file type: ${file.type}`)

          updateProgress?.(i * 100 + 100, fileArray.length * 100)

          completedCount++
          failedCount++
          continue
        }

        updateProgress?.(i * 100 + 20, fileArray.length * 100)

        let book = existingBooks?.find((b) => b.name === file.name)

        updateProgress?.(i * 100 + 40, fileArray.length * 100)

        const trackingSetLoading = (id: string | undefined) => {
          setLoading?.(id)

          if (id) {
            updateProgress?.(i * 100 + 60, fileArray.length * 100)
          } else {
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

        completedCount++
        updateProgress?.(completedCount * 100, fileArray.length * 100)
        updateSubTasks?.({
          filesCompleted: completedCount,
        })
      } catch (error) {
        console.error(`An error occurred while importing the file: ${error}`)

        completedCount++
        failedCount++
        updateProgress?.(completedCount * 100, fileArray.length * 100)
        updateSubTasks?.({
          filesCompleted: completedCount,
        })
      }
    }
  } finally {
    updateProgress?.(fileArray.length * 100, fileArray.length * 100)
    updateSubTasks?.({
      currentFileName: undefined,
      filesCompleted: completedCount,
    })
  }

  return { newBooks, success: successCount, failed: failedCount }
}
