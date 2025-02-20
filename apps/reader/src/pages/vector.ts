import { MemoryVectorStore } from 'langchain/vectorstores/memory'

// グローバル変数として vector store を保持する
let sharedVectorStore: MemoryVectorStore | null = null

export function setSharedVectorStore(store: MemoryVectorStore) {
  console.log('setSharedVectorStore', Boolean(store))
  sharedVectorStore = store
}

export function getSharedVectorStore(): MemoryVectorStore | null {
  console.log('getSharedVectorStore', Boolean(sharedVectorStore))
  return sharedVectorStore
}
