import type { Document } from '@langchain/core/documents'
import { StringOutputParser } from '@langchain/core/output_parsers'
import { RunnablePassthrough } from '@langchain/core/runnables'
import { RunnableSequence } from '@langchain/core/runnables'
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
      return Response.json({ error: 'question is required' }, { status: 400 })
    }

    // グローバルに保存している vector store を取得
    const vectorStore = getSharedVectorStore()
    if (!vectorStore) {
      console.error('Vector store is not available')
      return Response.json(
        { error: 'Vector store is not initialized' },
        { status: 500 },
      )
    }

    console.log('vectorStore', vectorStore)
    // retriever を使って、質問に関連するドキュメントを取得する
    const vectorStoreRetriever = vectorStore.asRetriever()

    console.log('process.env.OPENAI_API_KEY', process.env.OPENAI_API_KEY)
    const model = new ChatOpenAI({
      model: 'gpt-4o-mini',
      apiKey: process.env.OPENAI_API_KEY,
    })

    console.log('vectorStoreRetriever', vectorStoreRetriever)
    const chain = RunnableSequence.from([
      {
        context: vectorStoreRetriever.pipe((docs: Document[]) =>
          formatDocumentsAsString(docs),
        ),
        question: new RunnablePassthrough(),
      },
      ragPrompt,
      model,
      new StringOutputParser(),
    ])

    console.log('chain', chain)
    const answer = await chain.invoke(question)
    console.log('answer', answer)

    return res.status(200).json({ answer })
  } catch (error) {
    console.error('OpenAI API error:', error)
    return res.status(500).json({ error: 'Internal Server Error' })
  }
}
