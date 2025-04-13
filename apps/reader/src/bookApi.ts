import { fileToBase64 } from './fileUtils'
import { BookDetail } from './hooks/useLibrary'
import { TEST_USER_ID } from './pages/_app'

export async function fetchAllBooks(): Promise<BookDetail[]> {
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

export async function fetchBookById(
  bookId: string,
): Promise<BookDetail | null> {
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
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/books/${bookId}/file?user_id=${TEST_USER_ID}`,
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

export async function createBook(
  file: File,
  book: BookDetail,
  coverDataUrl: string | null = null,
): Promise<BookDetail | null> {
  const fileBase64 = await fileToBase64(file)

  const requestData = {
    file_data: fileBase64,
    file_name: file.name,
    file_type: file.type,
    user_id: TEST_USER_ID,
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
      return {
        id: responseData.data.id,
        name: responseData.data.name,
        size: responseData.data.size,
        author: responseData.data.author,
        metadata: book.metadata,
        createdAt: new Date(responseData.data.created_at).getTime(),
        updatedAt: new Date(responseData.data.updated_at).getTime(),
        cfi: responseData.data.cfi,
        percentage: responseData.data.percentage,
        definitions: responseData.data.definitions || [],
        annotations: responseData.data.annotations || [],
        configuration: responseData.data.configuration,
        hasCover: !!responseData.data.cover_path,
        tenant_id: responseData.data.tenant_id,
      }
    }
    return null
  } catch (error) {
    console.error('書籍登録中のエラー:', error)
    return null
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
