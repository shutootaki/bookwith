import fs from 'fs'
import path from 'path'

import { EPubLoader } from '@langchain/community/document_loaders/fs/epub'
import { OpenAIEmbeddings } from '@langchain/openai'
import { RecursiveCharacterTextSplitter } from 'langchain/text_splitter'
import { MemoryVectorStore } from 'langchain/vectorstores/memory'
import { NextApiRequest, NextApiResponse } from 'next'

import { setSharedVectorStore } from '../vector'
import formidable from 'formidable'

export const config = {
  api: {
    bodyParser: false,
  },
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse,
) {
  try {
    console.log('index-doc開始')

    // formidableでファイルを解析
    const form = formidable({
      keepExtensions: true,
      // maxFileSize: 10 * 1024 * 1024, // 10MB
    })

    const [_, files] = await form.parse(req)
    const file = files.file?.[0]

    if (!file) {
      return res
        .status(400)
        .json({ error: 'ファイルがアップロードされていません' })
    }

    const tmpDir = path.join(process.cwd(), 'tmp')
    await fs.promises.mkdir(tmpDir, { recursive: true })

    // formidableが一時保存したファイルを使用
    const filePath = file.filepath

    const docs = await new EPubLoader(filePath).load()
    const splitter = new RecursiveCharacterTextSplitter({
      chunkSize: 1000,
      chunkOverlap: 200,
    })
    const splitDocs = await splitter.splitDocuments(docs)
    const embeddings = new OpenAIEmbeddings({
      model: 'text-embedding-3-large',
      apiKey: process.env.OPENAI_API_KEY,
      maxRetries: 2,
    })
    const vectorStore = await MemoryVectorStore.fromDocuments(
      splitDocs,
      embeddings,
    )

    console.log('vectorStore', vectorStore)

    // グローバルな vector store として共通モジュールに保存
    setSharedVectorStore(vectorStore)

    return res.status(200).json({
      message: 'アップロードと処理が正常に完了しました',
      vectorStoreStatus: true,
    })
  } catch (error) {
    console.error('Error:', error)
    return res.status(500).json({ error: 'Internal Server Error' })
  }
}
