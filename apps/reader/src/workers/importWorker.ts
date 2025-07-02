import { createBook, fetchAllBooks } from '../lib/apiHandler/bookApiHandler'
import { components } from '../lib/openapi-schema/schema'
import { TEST_USER_ID } from '../pages/_app'
import { fileToEpub, indexEpub } from '../utils/epub'
import { fileToBase64, toDataUrl } from '../utils/fileUtils'
import { mapExtToMimes } from '../utils/mime'

type BookDetail = components['schemas']['BookDetail']

// Helper function to add book via API (originally in importHandlers.ts)
async function addBookToAPI(file: File): Promise<BookDetail | null> {
  // Notify main thread about progress
  postMessage({ type: 'progress', payload: { name: file.name, progress: 10 } })

  const epub = await fileToEpub(file)
  const metadata = await epub.loaded.metadata

  try {
    let coverDataUrl = null
    try {
      // Getting cover URL can fail
      const coverUrl = await epub.coverUrl()
      if (coverUrl) {
        coverDataUrl = await toDataUrl(coverUrl)
      }
    } catch (coverError) {
      console.warn(
        `Could not process cover image for ${file.name}:`,
        coverError,
      )
    }
    postMessage({
      type: 'progress',
      payload: { name: file.name, progress: 30 },
    })

    const bookRequest: components['schemas']['BookCreateRequest'] = {
      fileData: await fileToBase64(file),
      fileName: file.name,
      userId: TEST_USER_ID,
      bookName: file.name || `${metadata.title}.epub`,
      bookMetadata: JSON.stringify(metadata),
      coverImage: coverDataUrl || null,
    }
    postMessage({
      type: 'progress',
      payload: { name: file.name, progress: 50 },
    })

    const bookData = await createBook(bookRequest)
    postMessage({
      type: 'progress',
      payload: { name: file.name, progress: 70 },
    })

    if (!bookData) {
      console.error(`Failed to register book to API: ${file.name}`)
      return null
    }

    // Indexing might be heavy, ensure indexEpub is worker-compatible
    // or consider moving indexing to the server-side triggered by createBook.
    await indexEpub(file, TEST_USER_ID, bookData.id)
    postMessage({
      type: 'progress',
      payload: { name: file.name, progress: 90 },
    })

    return bookData
  } catch (error) {
    console.error(`Error occurred while registering book (${file.name}):`, error)
    throw error
  }
}

// Main function to handle files received from the main thread
async function handleFilesWorker(files: File[]) {
  const fileArray = files
  const newBooks: BookDetail[] = []
  let completedCount = 0
  let successCount = 0
  let failedCount = 0

  // Notify main thread: starting import
  postMessage({ type: 'start', payload: { total: fileArray.length } })

  // Fetch existing books list to avoid duplicates (API call from worker)
  let existingBooks: BookDetail[] = []
  try {
    existingBooks = (await fetchAllBooks()) || []
  } catch (error) {
    console.error('Worker: Failed to fetch existing books:', error)
    // Continue without checking for duplicates if fetch fails
  }

  for (let i = 0; i < fileArray.length; i++) {
    const file = fileArray[i]
    if (!file) continue

    // Helper to post progress for the current file
    const currentFileProgress = (progress: number) => {
      postMessage({
        type: 'fileProgress',
        payload: { name: file.name, progress, index: i },
      })
    }

    // Helper to update overall progress
    const updateOverall = () => {
      postMessage({
        type: 'updateOverall',
        payload: {
          completed: completedCount,
          success: successCount,
          failed: failedCount,
        },
      })
    }

    try {
      currentFileProgress(0) // Start processing this file

      // --- File Type Validation ---
      const isEpub = mapExtToMimes['.epub']?.includes(file.type)
      const isZip = mapExtToMimes['.zip']?.includes(file.type) // Check for ZIP

      if (!isEpub && !isZip) {
        console.warn(
          `Worker: Unsupported file type: ${file.type} (${file.name})`,
        )
        throw new Error(`Unsupported file type: ${file.type}`)
      }

      // --- Handle ZIP Files (Skip as per original logic) ---
      if (isZip) {
        console.log(`Worker: Skipping ZIP file: ${file.name}`)
        currentFileProgress(100) // Mark as completed immediately
        completedCount++
        // Note: Original logic didn't count ZIP as success/failure.
        updateOverall()
        continue // Move to the next file
      }

      // --- Handle EPUB Files ---
      currentFileProgress(20)
      let book: BookDetail | null | undefined = existingBooks?.find(
        (b) => b.name === file.name,
      )
      currentFileProgress(40)

      if (!book) {
        // Book doesn't exist, add it using the API helper
        book = await addBookToAPI(file) // Progress reported inside addBookToAPI
        if (book) {
          // Add to the locally fetched list to prevent re-adding if duplicated in the input list
          existingBooks.push(book)
        }
      } else {
        console.log(`Worker: Book already exists, skipping: ${file.name}`)
        // If the book exists, we might still want to show 100% progress for it
        currentFileProgress(100)
      }

      if (book) {
        newBooks.push(book) // Keep track of newly added/found books if needed
        successCount++
      } else if (!existingBooks?.some((b) => b.name === file.name)) {
        // Only count as failed if it wasn't an existing book that was skipped
        failedCount++
      }
      currentFileProgress(100) // Mark as completed (either added, existed, or failed)

      completedCount++
      updateOverall()
    } catch (error: any) {
      console.error(
        `Worker: ファイルのインポート中にエラーが発生しました (${file.name}): ${error}`,
      )
      currentFileProgress(100) // Mark as completed even on error
      failedCount++
      completedCount++
      updateOverall()
      // Notify main thread about the specific file error
      postMessage({
        type: 'error',
        payload: { name: file.name, message: error.message || String(error) },
      })
    }
  }

  // Notify main thread: all files processed
  postMessage({
    type: 'complete',
    payload: {
      total: fileArray.length,
      success: successCount,
      failed: failedCount /*, newBooks */,
    },
  }) // Sending newBooks back might be large
}

// Listen for messages from the main thread
self.onmessage = (event: MessageEvent<{ files: File[] }>) => {
  if (event.data && event.data.files) {
    handleFilesWorker(event.data.files).catch((err) => {
      console.error('Worker: Uncaught error during execution:', err)
      // Notify main thread about a fatal worker error
      postMessage({
        type: 'fatalError',
        payload: { message: err instanceof Error ? err.message : String(err) },
      })
    })
  }
}

// Initial message to confirm worker is ready (optional)
postMessage({ type: 'workerReady' })
