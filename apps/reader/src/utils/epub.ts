import ePub from '@flow/epubjs'

import { fileToBase64 } from './fileUtils'

export async function fileToEpub(file: File) {
  const data = await file.arrayBuffer()
  return ePub(data)
}

export const indexEpub = async (file: File, userId: string, bookId: string) => {
  try {
    await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/rag`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userId,
        bookId,
        fileData: await fileToBase64(file),
        fileName: file.name,
      }),
    })
  } catch (error) {
    console.error('アップロード中のエラー:', error)
  }
}
