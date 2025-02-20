import fs from 'fs'
import path from 'path'

import { EPubLoader } from '@langchain/community/document_loaders/fs/epub'
import { OpenAIEmbeddings } from '@langchain/openai'
import { RecursiveCharacterTextSplitter } from 'langchain/text_splitter'
import { MemoryVectorStore } from 'langchain/vectorstores/memory'
import { NextApiRequest, NextApiResponse } from 'next'

import { setSharedVectorStore } from '../vector'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse,
) {
  try {
    console.log('index-doc開始')

    // const formData = await req.body
    // console.log('formData読み込み')
    // const file = formData.file
    const file = req.body
    console.log('ファイル読み込み')
    if (!file) {
      return res
        .status(400)
        .json({ error: 'ファイルがアップロードされていません' })
    }

    console.log('ファイル読み込み完了')
    const buffer = Buffer.from(await (file as File).arrayBuffer())
    console.log('バッファー作成完了')

    const tmpDir = path.join(process.cwd(), 'tmp')
    if (!fs.existsSync(tmpDir)) {
      fs.mkdirSync(tmpDir)
    }
    const fileName = (file as File).name
    const filePath = path.join(tmpDir, fileName)

    // 一時ファイルとして保存
    await fs.promises.writeFile(filePath, new Uint8Array(buffer))
    // await fs.promises.writeFile(filePath, buffer)

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
