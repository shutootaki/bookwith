import type { Document } from '@langchain/core/documents'
import { StringOutputParser } from '@langchain/core/output_parsers'
import { RunnablePassthrough } from '@langchain/core/runnables'
import { RunnableSequence } from '@langchain/core/runnables'
import { VectorStoreRetriever } from '@langchain/core/vectorstores'
import { ChatOpenAI } from '@langchain/openai'
import { NextApiRequest, NextApiResponse } from 'next'

import { ragPrompt } from '../../prompts/prompts'
import { getSharedVectorStore } from '../vector'

export const formatDocumentsAsString = (documents: Document[]) => {
  return documents.map((document) => document.pageContent).join('\n\n')
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse,
) {
  try {
    const { question } = await req.body
    if (!question) {
      return res.status(400).json({ error: 'question is required' })
    }

    const model = new ChatOpenAI({
      model: 'gpt-4o-mini',
      apiKey: process.env.OPENAI_API_KEY,
    })
    // グローバルに保存している vector store を取得
    // todo: 永続化
    const vectorStore = getSharedVectorStore()
    let vectorStoreRetriever: VectorStoreRetriever
    // if (!vectorStore) {
    //   console.error('Vector store is not available')
    //   return res.status(500).json({ error: 'Vector store is not initialized' })
    // }
    if (vectorStore) {
      // retriever を使って、質問に関連するドキュメントを取得する
      vectorStoreRetriever = vectorStore.asRetriever()
    }

    const chain = RunnableSequence.from([
      {
        context: vectorStoreRetriever
          ? vectorStoreRetriever.pipe((docs: Document[]) =>
              formatDocumentsAsString(docs),
            )
          : new RunnablePassthrough(),
        question: new RunnablePassthrough(),
      },
      ragPrompt,
      model,
      new StringOutputParser(),
    ])

    const answer = await chain.invoke(question)

    return res.status(200).json({ answer })
  } catch (error) {
    console.error('OpenAI API error:', error)
    return res.status(500).json({ error: 'Internal Server Error' })
  }
}
