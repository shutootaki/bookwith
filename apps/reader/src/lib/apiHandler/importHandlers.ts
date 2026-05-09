import { v4 as uuidv4 } from 'uuid'

import { fileToEpub, indexEpub } from '../../utils/epub'
import { fileToBase64, toDataUrl } from '../../utils/fileUtils'
import { mapExtToMimes } from '../../utils/mime'
import { components } from '../openapi-schema/schema'

import { createBook, fetchAllBooks } from './bookApiHandler'

type BookDetail = components['schemas']['BookDetail']

const LOCAL_IMPORT_MAX_BYTES = 25 * 1024 * 1024
const ZIP_MAGIC_BYTES = [0x50, 0x4b, 0x03, 0x04] as const

async function readFirstBytes(file: File, length: number): Promise<Uint8Array> {
  const slice = file.slice(0, length)
  const buffer = await slice.arrayBuffer()
  return new Uint8Array(buffer)
}

export async function assertImportableEpubFile(file: File): Promise<void> {
  if (file.size > LOCAL_IMPORT_MAX_BYTES) {
    throw new RemoteImportError(
      `File exceeds the import size limit (${LOCAL_IMPORT_MAX_BYTES} bytes).`,
    )
  }
  if (file.size < ZIP_MAGIC_BYTES.length) {
    throw new RemoteImportError('File is too short to be a valid EPUB.')
  }
  const head = await readFirstBytes(file, ZIP_MAGIC_BYTES.length)
  if (!ZIP_MAGIC_BYTES.every((byte, i) => head[i] === byte)) {
    throw new RemoteImportError('File is not a valid EPUB / ZIP container.')
  }
}

const REMOTE_IMPORT_MAX_BYTES = LOCAL_IMPORT_MAX_BYTES
const PRIVATE_HOSTS = ['localhost', '127.0.0.1'] as const
const PRIVATE_HOST_PREFIXES = ['10.', '192.168.', '169.254.'] as const
const DEFAULT_REMOTE_IMPORT_HOSTS: ReadonlyArray<string> = ['cdn.bookwith.app']

function _envAllowedHosts(): readonly string[] {
  const raw = process.env.NEXT_PUBLIC_REMOTE_IMPORT_ALLOWED_HOSTS ?? ''
  return raw
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

const REMOTE_IMPORT_ALLOWED_HOSTS: ReadonlySet<string> = new Set([
  ...DEFAULT_REMOTE_IMPORT_HOSTS,
  ..._envAllowedHosts(),
])

export class RemoteImportError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'RemoteImportError'
  }
}

export function isAllowedRemoteImportUrl(rawUrl: string): boolean {
  let parsed: URL
  try {
    parsed = new URL(rawUrl)
  } catch {
    return false
  }
  const host = parsed.hostname
  return (
    parsed.protocol === 'https:' &&
    REMOTE_IMPORT_ALLOWED_HOSTS.has(host) &&
    !PRIVATE_HOSTS.some((privateHost) => host === privateHost) &&
    !PRIVATE_HOST_PREFIXES.some((prefix) => host.startsWith(prefix))
  )
}

function safeFilenameFromUrl(rawUrl: string): string {
  try {
    const parsed = new URL(rawUrl)
    const tail = parsed.pathname.split('/').pop() ?? ''
    const decoded = decodeURIComponent(tail)
    if (/\.epub$/i.test(decoded)) return decoded
  } catch {
    // ignore decode errors
  }
  return `import-${Date.now()}.epub`
}

export async function addBook(
  file: File,
  setLoading?: (id: string | undefined) => void,
): Promise<BookDetail | null> {
  await assertImportableEpubFile(file)

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

    const bookRequest = {
      fileData: await fileToBase64(file),
      fileName: file.name,
      bookId: tempBookId,
      bookName: file.name || `${metadata.title}.epub`,
      bookMetadata: JSON.stringify(metadata),
      coverImage: coverDataUrl || null,
    } as components['schemas']['BookCreateRequest']

    const bookData = await createBook(bookRequest)

    if (!bookData) {
      console.error('APIへの書籍登録に失敗しました')
      setLoading?.(undefined)
      return null
    }

    await indexEpub(file, bookData.id)

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
  if (!isAllowedRemoteImportUrl(url)) {
    throw new RemoteImportError('This URL is not allowed for remote import.')
  }

  const filename = safeFilenameFromUrl(url)

  const existingBooks = await fetchAllBooks()
  const book = existingBooks?.find((b) => b.name === filename)

  if (book) {
    return book
  }

  try {
    const res = await fetch(url, {
      mode: 'cors',
      redirect: 'error',
      credentials: 'omit',
    })
    if (!res.ok) {
      throw new Error(`Failed to fetch book from URL: ${res.statusText}`)
    }

    const contentType = res.headers.get('content-type') || ''
    if (
      !/application\/epub\+zip/i.test(contentType) &&
      !/application\/zip/i.test(contentType) &&
      !/application\/octet-stream/i.test(contentType)
    ) {
      throw new RemoteImportError(`Unexpected Content-Type: ${contentType}`)
    }
    const lengthHeader = res.headers.get('content-length')
    if (lengthHeader && Number(lengthHeader) > REMOTE_IMPORT_MAX_BYTES) {
      throw new RemoteImportError('Remote EPUB exceeds size limit')
    }

    const blob = await res.blob()
    if (blob.size > REMOTE_IMPORT_MAX_BYTES) {
      throw new RemoteImportError('Remote EPUB exceeds size limit')
    }
    return await addBook(new File([blob], filename), setLoading)
  } catch (error) {
    console.error(`Error fetching or adding book from URL ${url}:`, error)
    if (error instanceof RemoteImportError) {
      throw error
    }
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
