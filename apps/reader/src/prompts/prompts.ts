import { ChatPromptTemplate } from '@langchain/core/prompts'

const SYSTEM_TEMPLATE = `Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
----------------
{context}`

export const ragPrompt = ChatPromptTemplate.fromMessages([
  ['system', SYSTEM_TEMPLATE],
  ['human', '{question}'],
])
