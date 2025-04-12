import { v4 as uuidv4 } from 'uuid'

import ePub from '@flow/epubjs'

import { BookRecord } from './db'
import { mapExtToMimes } from './mime'
import { unpack } from './sync'

export async function fileToEpub(file: File) {
  const data = await file.arrayBuffer()
  return ePub(data)
}

export async function handleFiles(
  files: Iterable<File>,
  setLoading?: (id: string | undefined) => void,
) {
  const newBooks = []

  for (const file of files) {
    if (mapExtToMimes['.zip'].includes(file.type)) {
      unpack(file)
      continue
    }

    if (!mapExtToMimes['.epub'].includes(file.type)) {
      console.error(`Unsupported file type: ${file.type}`)
      continue
    }

    // 既存の書籍を検索するためにAPIを呼び出す
    const existingBooks = await fetchAllBooks()
    let book = existingBooks?.find((b) => b.name === file.name)

    if (!book) {
      book = (await addBook(file, setLoading)) || undefined
    }

    if (book) {
      newBooks.push(book)
    }
  }

  return newBooks
}

// すべての書籍を取得するAPIを呼び出す
export async function fetchAllBooks(): Promise<BookRecord[]> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/books`,
    )
    if (!response.ok) {
      console.error('書籍一覧取得エラー:', await response.json())
      return []
    }

    const responseData = await response.json()
    if (responseData?.success && Array.isArray(responseData?.data)) {
      // APIから返されたデータをBookRecordに変換して返す
      return responseData.data.map((book: any) => ({
        id: book.id,
        name: book.name,
        author: book.author,
        size: book.size,
        metadata: book.book_metadata,
        createdAt: new Date(book.created_at).getTime(),
        updatedAt: book.updated_at
          ? new Date(book.updated_at).getTime()
          : undefined,
        cfi: book.cfi,
        percentage: book.percentage || 0,
        definitions: book.definitions || [],
        annotations: [],
        configuration: book.configuration,
        hasCover: book.has_cover || false,
      }))
    }
    return []
  } catch (error) {
    console.error('書籍一覧取得中のエラー:', error)
    return []
  }
}

// 特定の書籍情報を取得するAPIを呼び出す
export async function fetchBookById(
  bookId: string,
): Promise<BookRecord | null> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/books/${bookId}`,
    )
    if (!response.ok) {
      console.error('書籍取得エラー:', await response.json())
      return null
    }

    const responseData = await response.json()
    if (responseData?.success && responseData?.data) {
      const book = responseData.data
      // APIから返されたデータをBookRecordに変換して返す
      return {
        id: book.id,
        name: book.name,
        author: book.author,
        size: book.size,
        metadata: book.book_metadata,
        createdAt: new Date(book.created_at).getTime(),
        updatedAt: book.updated_at
          ? new Date(book.updated_at).getTime()
          : undefined,
        cfi: book.cfi,
        percentage: book.percentage || 0,
        definitions: book.definitions || [],
        annotations: [],
        configuration: book.configuration,
        hasCover: book.has_cover || false,
      }
    }
    return null
  } catch (error) {
    console.error('書籍取得中のエラー:', error)
    return null
  }
}

export async function addBook(
  file: File,
  setLoading?: (id: string | undefined) => void,
) {
  // EPUBファイルからメタデータを取得
  const epub = await fileToEpub(file)
  const metadata = await epub.loaded.metadata

  // 一時的なブックIDを生成（サーバーからのレスポンスで置き換える可能性あり）
  const tempBookId = uuidv4()
  setLoading?.(tempBookId)

  try {
    // カバー画像を取得してデータURLに変換
    const coverUrl = await epub.coverUrl()
    let coverDataUrl = null
    if (coverUrl) {
      coverDataUrl = await toDataUrl(coverUrl)
    }

    // APIに書籍を登録
    const bookData = await createBookInAPI(
      file,
      {
        id: tempBookId,
        name: file.name || `${metadata.title}.epub`,
        size: file.size,
        metadata,
        createdAt: Date.now(),
        definitions: [],
        annotations: [],
      },
      coverDataUrl,
    )

    if (!bookData) {
      console.error('APIへの書籍登録に失敗しました')
      return null
    }

    // await indexEpub(file, bookData.id)

    setLoading?.(undefined)
    return bookData
  } catch (error) {
    console.error('書籍の登録中にエラーが発生しました:', error)
    setLoading?.(undefined)
    return null
  }
}

// APIに書籍を登録する関数
export async function createBookInAPI(
  file: File,
  book: BookRecord,
  coverDataUrl: string | null = null,
): Promise<BookRecord | null> {
  // ファイルをBase64エンコードに変換
  const fileBase64 = await fileToBase64(file)

  const requestData = {
    file_data: fileBase64,
    file_name: file.name,
    file_type: file.type,
    user_id: 'test_user_id', // 実際のユーザーID管理に合わせて変更
    book_id: book.id,
    book_name: book.name,
    book_metadata: book.metadata ? JSON.stringify(book.metadata) : null,
    cover_image: coverDataUrl || null,
  }

  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/books`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      },
    )

    if (!response.ok) {
      const errorData = await response.json()
      console.error('書籍登録エラー:', errorData)
      return null
    }

    const responseData = await response.json()
    if (responseData?.success && responseData?.data) {
      // APIから返されたデータをBookRecordに変換して返す
      return {
        id: responseData.data.id,
        name: responseData.data.name,
        size: responseData.data.size,
        author: responseData.data.author,
        metadata: book.metadata, // APIからのレスポンスにはメタデータの詳細が含まれていない可能性があるため
        createdAt: new Date(responseData.data.created_at).getTime(),
        updatedAt: new Date(responseData.data.updated_at).getTime(),
        cfi: responseData.data.cfi,
        percentage: responseData.data.percentage,
        definitions: responseData.data.definitions || [],
        annotations: responseData.data.annotations || [],
        configuration: responseData.data.configuration,
        hasCover: !!responseData.data.cover_path,
      }
    }
    return null
  } catch (error) {
    console.error('書籍登録中のエラー:', error)
    return null
  }
}

// ファイルをBase64に変換する関数
async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => {
      const result = reader.result as string
      // データURLの先頭部分 (data:application/pdf;base64,) を削除して純粋なBase64を取得
      const base64 = result.split(',')[1]
      resolve(base64 || '')
    }
    reader.onerror = (error) => reject(error)
  })
}

export function readBlob(fn: (reader: FileReader) => void) {
  return new Promise<string>((resolve) => {
    const reader = new FileReader()
    reader.addEventListener('load', () => {
      resolve(reader.result as string)
    })
    fn(reader)
  })
}

async function toDataUrl(url: string) {
  const res = await fetch(url)
  const buffer = await res.blob()
  return readBlob((r) => r.readAsDataURL(buffer))
}

export async function fetchBook(
  url: string,
  setLoading?: (id: string | undefined) => void,
) {
  const filename = decodeURIComponent(/\/([^/]*\.epub)$/i.exec(url)?.[1] ?? '')

  // APIを通じて既存の書籍を検索
  const existingBooks = await fetchAllBooks()
  const book = existingBooks?.find((b) => b.name === filename)

  return (
    book ??
    fetch(url)
      .then((res) => res.blob())
      .then((blob) => addBook(new File([blob], filename), setLoading))
  )
}

const indexEpub = async (file: File, bookId: string) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('user_id', 'test_user_id')
  formData.append('book_id', bookId)

  try {
    await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/rag`, {
      method: 'POST',
      body: formData,
    })
  } catch (error) {
    console.error('アップロード中のエラー:', error)
  }
}

interface BookFileResponse {
  success: boolean
  url?: string
  error?: string
}

interface BookFileData {
  id: string
  file: File
}

export const getBookFile = async (
  bookId: string,
): Promise<BookFileData | undefined> => {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/books/${bookId}/file?user_id=test_user_id`,
    )
    if (!response.ok)
      throw new Error(
        `書籍ファイルの取得に失敗しました: ${response.statusText}`,
      )

    const data: BookFileResponse = await response.json()
    if (!data.success || !data.url)
      throw new Error('ブックファイルのURLが取得できませんでした')

    const fileResponse = await fetch(data.url)
    if (!fileResponse.ok)
      throw new Error(
        `ファイルのダウンロードに失敗しました: ${fileResponse.statusText}`,
      )

    const blob = await fileResponse.blob()
    const fileName = data.url.split('/').pop() || 'book.epub'
    const file = new File([blob], fileName, { type: 'application/epub+zip' })

    return { id: bookId, file }
  } catch (error) {
    console.error('書籍ファイルの取得に失敗しました:', error)
    return undefined
  }
}

export async function deleteBooksFromAPI(bookIds: string[]): Promise<string[]> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/books/bulk-delete`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ book_ids: bookIds }),
      },
    )

    if (!response.ok) {
      console.error('書籍一括削除エラー:', await response.json())
      return []
    }

    const data = await response.json()
    return data.deletedIds || []
  } catch (error) {
    console.error('書籍一括削除中のエラー:', error)
    return []
  }
}
