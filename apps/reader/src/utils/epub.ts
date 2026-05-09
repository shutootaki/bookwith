import ePub from '@flow/epubjs'

import { apiClient } from '../lib/apiHandler/apiClient'

import { fileToBase64 } from './fileUtils'

export async function fileToEpub(file: File) {
  const data = await file.arrayBuffer()
  return ePub(data)
}

export const indexEpub = async (file: File, bookId: string) => {
  try {
    await apiClient('/rag', {
      method: 'POST',
      body: {
        bookId,
        fileData: await fileToBase64(file),
        fileName: file.name,
      },
    })
  } catch (error) {
    console.error('アップロード中のエラー:', error)
  }
}
