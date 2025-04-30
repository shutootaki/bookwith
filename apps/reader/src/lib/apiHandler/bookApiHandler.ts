import { TEST_USER_ID } from '../../pages/_app'
import { components } from '../openapi-schema/schema'

import { apiClient } from './apiClient'

type BookCreateRequest = components['schemas']['BookCreateRequest']
type BooksResponse = components['schemas']['BooksResponse']
type BookResponse = components['schemas']['BookResponse']
type BookFileResponse = components['schemas']['BookFileResponse']
type BulkDeleteResponse = components['schemas']['BulkDeleteResponse']
type BookDetail = components['schemas']['BookDetail']

/**
 * Fetches all books from the API.
 * Returns data directly conforming to the BookDetail schema.
 * @returns A promise that resolves to an array of BookDetail or an empty array on error.
 */
export async function fetchAllBooks(): Promise<BookDetail[]> {
  try {
    const responseData = await apiClient<BooksResponse>(
      `/books/user/${TEST_USER_ID}`,
      {
        method: 'GET',
      },
    )
    return responseData?.books || []
  } catch (error) {
    console.error('Error fetching all books:', error)
    return []
  }
}

/**
 * Gets the download URL for a book file and then fetches the file itself.
 * @param bookId The ID of the book to fetch.
 * @returns A promise resolving to {id: string, file: File} or undefined if an error occurs.
 */
export const getBookFile = async (
  bookId: string,
): Promise<
  | {
      id: string
      file: File
    }
  | undefined
> => {
  try {
    const responseData = await apiClient<BookFileResponse>(
      `/books/${bookId}/file`,
      { method: 'GET' },
    )

    const fileUrl = responseData?.url
    if (!fileUrl) {
      throw new Error('Book file URL not found in API response.')
    }

    const fileResponse = await fetch(fileUrl)
    if (!fileResponse.ok) {
      throw new Error(
        `Failed to download file from ${fileUrl}: ${fileResponse.status} ${fileResponse.statusText}`,
      )
    }

    const blob = await fileResponse.blob()
    const fileName = fileUrl.split('/').pop() || `book_${bookId}.epub`
    const file = new File([blob], fileName, { type: 'application/epub+zip' })

    return { id: bookId, file }
  } catch (error) {
    console.error(`Error getting book file for ID ${bookId}:`, error)
    return undefined
  }
}

/**
 * Creates a new book entry via the API.
 * Returns data directly conforming to the BookDetail schema.
 * @param bookRequest Data for the new book, conforming to BookCreateRequest schema.
 * @returns A promise resolving to the created BookDetail or null on error.
 */
export async function createBook(
  bookRequest: BookCreateRequest,
): Promise<BookDetail | null> {
  try {
    const responseData = await apiClient<BookResponse>('/books', {
      method: 'POST',
      body: bookRequest,
    })

    const createdApiBook = responseData?.bookDetail
    if (!createdApiBook) {
      console.error('API did not return book data after creation.')
      return null
    }

    return createdApiBook
  } catch (error) {
    console.error('Error creating book:', error)
    return null
  }
}

/**
 * Deletes multiple books via the API using their IDs.
 * @param bookIds An array of book IDs to delete.
 * @returns A promise resolving to an array of successfully deleted book IDs.
 */
export async function deleteBooksFromAPI(bookIds: string[]): Promise<string[]> {
  try {
    const responseData = await apiClient<BulkDeleteResponse>(
      '/books/bulk-delete',
      {
        method: 'DELETE',
        body: { book_ids: bookIds },
      },
    )

    return responseData?.deletedIds || []
  } catch (error) {
    console.error('Error deleting books:', error)
    return []
  }
}
