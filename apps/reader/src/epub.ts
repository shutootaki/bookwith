import ePub from '@flow/epubjs'

export async function fileToEpub(file: File) {
  const data = await file.arrayBuffer()
  return ePub(data)
}

export const indexEpub = async (file: File, bookId: string) => {
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
